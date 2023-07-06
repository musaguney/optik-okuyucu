import glob
import json
from imutils.perspective import four_point_transform
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import utils
import pandas as pd
import sys
import time
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow,QMessageBox,QMessageBox,QLabel
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal,Qt,QTimer
from anasayfa_python import Ui_MainWindow
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QTableWidgetItem


    

global cevapanahtariGercek,data,row,dataYanlis,rowYanlis,gorselAdiHata
data=[]
dataYanlis=[]
gorselAdiHata=""
global klasor_adi,secimtarzi
secimtarzi="optikokuma"
class optikThread(QThread):
    global klasor_adi,secimtarzi,gorselAdiHata
    sonuclariAl = pyqtSignal(str)
    cevapAnahtariAl=pyqtSignal(str)
    finish=pyqtSignal(str)
    
   
    def __init__(self):
        super().__init__()

    def run(self):
        global klasor_adi,secimtarzi
        



        global hassaslik,img,biggestContour_1
        # Hassaslık eşiği belirliyoruz.
        hassaslik =1800 # Hassaslık eşiği
        hassaslik=float(hassaslik)
        if(secimtarzi=="optikokuma"):
            images = glob.glob(klasor_adi+'/*.jpg')
        else:
            
            images=[]
            images.append(secimtarzi)
        
        
        
        
        heightImg = 1357
        widthImg  = 1025
     

        
        def disHattiBul(resimgeldi):
            global img,biggestContour_1
            
            try:      
                #Gelen resim yolunu aldık. Örn aşağıdaki gibi.
                #resimgeldi="ornekler2/a/A1.jpg"
                
                # Görüntüyü okuma ve boyutlandırma
                img= cv2.imread(resimgeldi)
                img= cv2.resize(img,(widthImg,heightImg))
                
                # Görüntü üzerinde konturları çizmek için kopyalarını oluşturma
                imgContours = img.copy()
                imgBiggestContours = img.copy()
                print("gorsel okunabildi")
                
                # Görüntüyü gri tonlamaya dönüştürdük.
                imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
                
                # Görüntüyü bulanıklaştırdık.
                imgBlur = cv2.GaussianBlur(imgGray,(5,5),1)
                # Canny kenar tespiti 
                imgCanny = cv2.Canny(imgBlur,10,50)
                # Konturları bulma
                contours, hierarchy = cv2.findContours(imgCanny,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
                # Konturları görüntü üzerine çizdirdik
                cv2.drawContours(imgContours,contours,-1,(0,255,0),10)
                # Dikdörtgen konturu bulma
                rectCon= utils.rectContour(contours)
                # En büyük konturun köşe noktalarını aldık
                biggestContour_1 = utils.getCornerPoints(rectCon[0])
                # En büyük konturu görüntü üzerine çizdirdik
                cv2.drawContours(imgBiggestContours,biggestContour_1,-1,(0,255,0),20)
                
           
                return True
            except:     
                return "Dış Hat Bulunamadı"
        
        
        def koseleriBul():
            global biggestContour
            imgBiggestContours = img.copy()
        
            # En büyük konturu yeni bir değişkene kopyalama
            biggestContour_yeni=biggestContour_1
            
            # En büyük konturu görüntü üzerine çizme
            cv2.drawContours(imgBiggestContours,biggestContour_yeni,-1,(255,0,59),20)
            # Köşeleri bulma ve yeniden düzenleme
            biggestContour=utils.reorder(biggestContour_yeni)
        
        
            
        
        def renkdegistirveisle():
            global crop_img_1
            heightImg = 650
            widthImg  = 2350
           # Perspektif dönüşümü için görüntünün boyutları belirlenir
           # heightImg ve widthImg değerleri kullanılır.
         
            # Dönüşüm matrisi için başlangıç ve hedef noktaları tanımlanır
            pt1= np.float32(biggestContour)
            pt2 = np.float32([[0,10],[widthImg,0],[0,heightImg],[widthImg,heightImg]])
            matrix = cv2.getPerspectiveTransform(pt1,pt2)
            # Perspektif dönüşümü uygulanarak yeni bir görüntü oluşturulur
            imgWarpColored= cv2.warpPerspective(img,matrix,(widthImg,heightImg))
           # Oluşturulan görüntü crop_img_1 değişkenine atanır
            crop_img_1 = imgWarpColored

        def splitBoxes(veri,row,column):
            # Veriyi belirtilen satır ve sütun sayısına göre böler
            rows = np.vsplit(veri,row) # Veriyi satırlara böldük.
            boxes =[]
            for r in rows:
                cols = np.hsplit(r,column) # Satırdaki veriyi sütunlara böldü
                 
                for box in cols:
                    boxes.append(box) # Her bir kutuyu boxes listesine ekledi.
                     
            return boxes
        
        def pikselleriDoldur(boxes,row,column):
         
            countC=0
            countR=0
            cvp_sil=[]
            # Her bir kutu için piksel sayısını hesaplar ve cvp_sil listesine ekler
            for image in boxes:
                totalPixels = cv2.countNonZero(image)
                cvp_sil.append(totalPixels)
          # cvp_sil listesini numpy dizisine dönüştürür ve satır/sütun şeklinde yeniden şekillendirir
            cvp_sil=np.array(cvp_sil)
            cvp_sil=cvp_sil.reshape(row,column)
            
            myPixelVal=cvp_sil
            return myPixelVal
        
        
        def ogrenciNumarasiSon(myPixelVal):
            student_number = ''
        
            # Her sütundaki en yüksek değere sahip satırın indeksini bul
            for column in myPixelVal.T:
                max_value = np.max(column)
                two_largest_values = np.partition(column, -2)[-2:]  # Satırdaki en büyük iki değeri bul
        
                # Eğer maksimum değer belirli bir eşik değerinin altındaysa, bu durum boş bırakılmış bir soru olarak kabul edilir.
                if max_value < hassaslik:
                    student_number += 'X'  # 'X' boş bırakılan bir soruyu temsil eder.
                else:
                    # Eğer bir satırda birden fazla maksimum değer varsa, bu durum çift işaretleme olarak kabul edilir.
                    if np.count_nonzero(column == max_value) > 1:
                        student_number += 'X'  # 'X' hatalı yanıt verilen bir soruyu temsil eder.
                    elif np.abs(two_largest_values[0] - two_largest_values[1]) / two_largest_values[1] < 0.1:  # Eğer iki değer arasındaki fark %10'dan azsa
                        student_number += 'X'
                    elif (two_largest_values[0]>4000 and two_largest_values[1]>4000):
                        student_number += 'X'
                    else:
                        digit = np.argmax(column)
                        student_number += str(digit)
                
            return student_number
        
        def derslerincevaplarinial(myPixelVal):
            answers = ''
            alphabet = 'ABCDE'  # İndekslerin alfabedeki karşılıklarını bulmak için bir dizi
            
            
            # Her satırdaki en yüksek değere sahip sütunların indekslerini bul
            for row in myPixelVal:
                max_value = np.max(row)
                two_largest_values = np.partition(row, -2)[-2:]  # Satırdaki en büyük iki değeri bul
        
                # Eğer maksimum değer belirli bir eşik değerinin altındaysa, bu durum boş bırakılmış bir soru olarak kabul edilir.
                if max_value < hassaslik:
                    answers += 'X'  # 'X' boş bırakılan bir soruyu temsil eder.
                else:
                    # Eğer bir satırda birden fazla maksimum değer varsa, bu durum çift işaretleme olarak kabul edilir.
                    if np.count_nonzero(row == max_value) > 1:
                        answers += 'X'  # 'X' çift işaretlemeyi temsil eder.
                    elif (
                            (np.abs(two_largest_values[0] - two_largest_values[1]) / two_largest_values[1] < 0.09)):  # Eğer iki değer arasındaki fark %10'dan azsa
                        answers += 'X'
                    else:
                        index = np.argmax(row)
                        answers += alphabet[index]
            
            print(f"Cevaplar: {answers}")
            return answers
        
        def sorulariisle(sorular_1):
            gray = cv2.cvtColor(sorular_1, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255,
            	cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            
            boxes=splitBoxes(thresh,10,5)
            myPixelVal=np.zeros((10,5))
            myPixelVal=pikselleriDoldur(boxes,10,5)
            print(myPixelVal)
            return myPixelVal
        
        def sorular(sol,sag):
            sorular_1=crop_img_1[220:635, sol:sag]
            sorular_1 = cv2.resize(sorular_1, (280, 630)) 
            return sorulariisle(sorular_1)
        
        def ogrNoBulma():
            # Öğrenci numarasını içeren bölgenin kesimi
            ogrnoimg=crop_img_1[230:640, 5:635]
            # Görüntünün boyutunu yeniden boyutlandırma
            ogrnoimg = cv2.resize(ogrnoimg, (1280, 640)) 
            # Görüntüyü gri tonlamalı hale getirme
            gray = cv2.cvtColor(ogrnoimg, cv2.COLOR_BGR2GRAY)
        
            # Gri görüntüyü eşikleme işlemine tabi tutma
            thresh = cv2.threshold(gray, 0, 255,
            	cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            # Kutucuklara bölme işlemi
            boxes=splitBoxes(thresh,10,10)
           # Piksel değerlerini tutmak için 10x10 boyutunda bir dizi oluşturma
            myPixelVal=np.zeros((10,10))
            # Her bir kutucuğun piksel değerlerini doldurma
            myPixelVal=pikselleriDoldur(boxes,10,10)
            # Piksel değerlerini ekrana yazdırma
            print("ogrencino pikselleri")
            print(myPixelVal)
            # Öğrenci numarasını çıkarma
            ogrenciNumarasi=ogrenciNumarasiSon(myPixelVal)
            # Öğrenci numarasını ekrana yazdırma
            print(f"Öğrenci Numarası: {ogrenciNumarasi}")
            # Öğrenci numarasını döndürme
            return ogrenciNumarasi
            

            
        def sorularibul():   
            # İlk soru grubunun sol ve sağ sınırlarını belirle
            b=765
            # İlk soru grubunun cevaplarını hesapla
            cevap1=derslerincevaplarinial(sorular(b,b+270))
            # İkinci soru grubunun sol ve sağ sınırlarını belirle
            b=b+270+150
           # İkinci soru grubunun cevaplarını hesapla
            cevap2=derslerincevaplarinial(sorular(b,b+270))
            # Üçüncü soru grubunun sol ve sağ sınırlarını belirle
            b=b+270+150
            # Üçüncü soru grubunun cevaplarını hesapla
            cevap3=derslerincevaplarinial(sorular(b,b+270))
            # Dördüncü soru grubunun sol ve sağ sınırlarını belirle
            b=b+270+150
            # Dördüncü soru grubunun cevaplarını hesapla
            cevap4=derslerincevaplarinial(sorular(b,b+270))
            # Hesaplanan cevapları birleştir
            return cevap1+cevap2+cevap3+cevap4
               
        
        def start():
            #basla
            for resimgeldi in images:
                gorselAdiHata=resimgeldi
                sonuc=disHattiBul(resimgeldi)
                
                if(sonuc==True):   
                    print(resimgeldi)
                    koseleriBul()
                    renkdegistirveisle()
                    ogrenciNumarasi=ogrNoBulma()
                    sorular=sorularibul()
                    if(secimtarzi=="optikokuma"):
                        self.sonuclariAl.emit(ogrenciNumarasi+";"+sorular)
                    else:
                        self.cevapAnahtariAl.emit(sorular)
                else:
                    
                    rowYanlis = {
                         'ogrenciNo': "ogrno",
                         'Cevaplar': "dogru_yanlis_str",
                         'Puan': "toplam_puan",
                         'gorseladi': gorselAdiHata
                     }
                    dataYanlis.append(rowYanlis)
                    
                    self.cevapAnahtariAl.emit("")
                  
        
        
        
        

        start()
        self.finish.emit("")
        
  
        
        
class MainWindow(QMainWindow):
           def __init__(self):
               super(MainWindow, self).__init__()
               self.ui = Ui_MainWindow()
               self.ui.setupUi(self)
               self.setWindowTitle("Optik Okuma")
               self.setWindowFlags(Qt.WindowStaysOnTopHint)
               self.ui.dosya_yukle.clicked.connect(self.dosya_yukle)    
               self.ui.baslat.clicked.connect(self.baslat)    
               self.ui.dosya_yukle_2.clicked.connect(self.dosya_yukle_2)    
               self.ui.sorusayisi.textChanged.connect(self.sorusayisiDegisti)
               self.ui.comboBox.currentIndexChanged.connect(self.degerSecildi)
               
               
              
               pixmap = QPixmap("klu.jpg")  # Eklemek istediğimiz dosya yolunu yazdık.
               self.ui.resim.setPixmap(pixmap)
               self.ui.resim.setScaledContents(True)

           def sorusayisiDegisti(self):
               print(self.ui.sorusayisi.toPlainText())
               try:
                   self.ui.cevapanahtari.setRowCount(int(self.ui.sorusayisi.toPlainText()))
               except:
                   self.ui.cevapanahtari.setRowCount(40)
           
           def degerSecildi(self, index):
                secilen_deger = int(self.ui.comboBox.itemText(index))
                row_count = self.ui.cevapanahtari.rowCount()
                column_count = self.ui.cevapanahtari.rowCount()
        
                for col in range(column_count):
                    self.ui.cevapanahtari.setItem(col, 1, QTableWidgetItem(str(secilen_deger)))
                
           def dosya_yukle(self):
               global myworker
               global klasor_adi,secimtarzi
               
               dosya_adi, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Resim Dosyaları (*.png *.jpg *.bmp)")
            
               if dosya_adi:
                  # Seçilen dosya işlemleri burada yapılabilir
                  print("Seçilen dosya:", dosya_adi)
                  secimtarzi=dosya_adi
                  self.myworker = optikThread() 
                  self.myworker.cevapAnahtariAl.connect(self.cevapAnahtariAl)
                  self.myworker.start()
               
           def cevapAnahtariAl(self,veri):
                global cevapanahtariGercek,puanlar
               
                veri_listesi = list(veri)
        
                cevapanahtariGercek=veri_listesi
                
                for i in range(0,40):
                    try:
                        hucre = QTableWidgetItem("")
                        self.ui.cevapanahtari.setItem(i, 0, hucre)
                    except:
                        break
                
                for i in range(0,40):
                    try:
                        hucre = QTableWidgetItem(veri_listesi[i])
                        self.ui.cevapanahtari.setItem(i, 0, hucre)
                    except:
                        break
                    
               
           def  dosya_yukle_2(self):
                global klasor_adi,secimtarzi

                klasor_adi = QFileDialog.getExistingDirectory(self, "Klasör Seç")
                secimtarzi="optikokuma"
               
                    
           def sonuclariAl(self,veri):
               global cevapanahtariGercek,puanlar,data,row,dataYanlis,rowYanlis,gorselAdiHata
               
               #burada csv ye yazacağız
               ogrno=veri.split(";")[0]
               cevaplar=veri.split(";")[1]
               cevaplar = list(cevaplar)
               print(ogrno)

               
              
               
               def puan_hesapla(sorularin_gelen_cevaplari, cevaplar, puanlar):
                    dogru_yanlis_listesi = []
                    toplam_puan = 0
                    
                    for i in range(len(sorularin_gelen_cevaplari)):
                        if i >= len(cevaplar) or i >= len(puanlar):
                            break
                    
                        if sorularin_gelen_cevaplari[i] == cevaplar[i] and cevaplar[i] != 'X':
                            dogru_yanlis_listesi.append(True)
                            if puanlar[i]:
                                toplam_puan += int(puanlar[i])
                        else:
                            
                            if(sorularin_gelen_cevaplari[i]=="X"):
                               dogru_yanlis_listesi.append("BOS")

                            else:    
                                dogru_yanlis_listesi.append("False")
                    
                    return dogru_yanlis_listesi, toplam_puan



               dogru_yanlis, toplam_puan = puan_hesapla(cevaplar, cevapanahtariGercek, puanlar)
               

               dogru_yanlis_str = ' '.join(str(elem) for elem in dogru_yanlis)
               if "X" in ogrno:
                   rowYanlis = {
                        'ogrenciNo': ogrno,
                        'Cevaplar': dogru_yanlis_str,
                        'Puan': toplam_puan,
                        'gorseladi': gorselAdiHata
                    }
                   dataYanlis.append(rowYanlis)
                   
               else:
                   row = {
                        'ogrenciNo': ogrno,
                        #'Cevaplar': dogru_yanlis_str,
                        'Puan': toplam_puan
                    }
                   data.append(row)
               
               print("cevap anahtari:", cevaplar)
               print("cevaplar:", cevapanahtariGercek)
               print("Doğru/Yanlış Durumu:", dogru_yanlis)
               print("Toplam Puan:", toplam_puan)
                                
                               
           def finish(self):
               klasor_adi1 = QFileDialog.getExistingDirectory(self, "Klasör Seç")
               if klasor_adi1:
                  # Seçilen dosya işlemleri burada yapılabilir
                  print("Seçilen dosya:", klasor_adi1)
               
               df = pd.DataFrame(data)
               df.to_csv(klasor_adi1+"/"+self.ui.dersinadi.toPlainText()+".csv", index=False)
               
               df = pd.DataFrame(dataYanlis)
               df.to_csv(klasor_adi1+"/"+"hatalar"+self.ui.dersinadi.toPlainText()+".csv", index=False)
               
           def baslat(self):
                global klasor_adi,secimtarzi,puanlar,cevapanahtariGercek,data,dataYanlis
                data=[]
                dataYanlis=[]
                secimtarzi="optikokuma"
                if klasor_adi:
                    # Seçilen klasörde yapılacak işlemler burada gerçekleştirilebilir
                    #puanları okuyor.
                    puanlar=[]
                    for i in range(40):
                        try:
                            hucre = self.ui.cevapanahtari.item(i, 1)
                            if hucre is not None:
                                veri = hucre.text()
                                puanlar.append(veri)
                            else:
                                break
                        except:
                            break
                    
                    cevapanahtariGercek=[]
                    for i in range(40):
                        try:
                            hucre = self.ui.cevapanahtari.item(i, 0)
                            if hucre is not None:
                                veri = hucre.text()
                                cevapanahtariGercek.append(veri)
                            else:
                                break
                        except:
                            break

                    
                    
                    self.myworker2 = optikThread() 
                    self.myworker2.sonuclariAl.connect(self.sonuclariAl)
                    self.myworker2.finish.connect(self.finish)
                    self.myworker2.start()


if __name__ == "__main__":
        app = QApplication(sys.argv)

        window = MainWindow()
        window.setWindowTitle("Optik Okuma")
        window.show()

        sys.exit(app.exec_())
        




        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
