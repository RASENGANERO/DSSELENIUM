# -*- coding: cp1251-*-
import os
from flask import Flask, jsonify
from flask_cors import CORS
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import threading
from pprint import pprint
from flask import request
import time
import random
import requests
from PIL import Image
import base64
import pymysql
import paramiko

connect = pymysql.connect(host='194.67.126.178',
                          user='root',
                          password='rasengan23',
                          database='getvisa',
                          charset='utf8mb4',
                          cursorclass=pymysql.cursors.DictCursor)
cursor=connect.cursor()



class StartDSRecord:

    def __init__(self,data):
        self.datas=data
        self.objectname=None
        self.driver=None
        self.TWOCAPTCHA_API_KEY = '2d77ec701ee5c539ec02a43e8e6467f2'
        self.barcode=""
        
    def GetData(self,dtn):
        cursor.execute("SELECT *FROM DS WHERE Id="+"'"+str(dtn)+"'")
        data = cursor.fetchone()
        return data


    def CaptchaPage(self):
        try:
            encoded_string =""
            with open('D:/'+str(self.objectname).strip()+'.png', "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())   
            params = dict(key=self.TWOCAPTCHA_API_KEY, method='base64', body=encoded_string, json=1)
            res = requests.post('https://rucaptcha.com/in.php', params).json()
            time.sleep(5)
            paramsget=dict(key=self.TWOCAPTCHA_API_KEY, action="get",id=res["request"])
            answer=""
            error=""
            while True:
                resq=requests.get('https://rucaptcha.com/res.php', paramsget)
                if resq.text=="CAPCHA_NOT_READY":
                    error=""
                    continue
                if str(resq.text).startswith("OK|")==True:
                    answer=str(resq.text).split("|")[1].strip()
                    error=""
                    break
                else:
                    error=resq.text
                    break
            return [error,answer]
        except Exception:
            time.sleep(5)
            self.CaptchaPage()

    def convertData(self,filename):
        with open(filename, 'rb') as file:
            data = file.read()
        return data

    def GenerateData(self,s):
        return str(s).split("--->")



    def SetFinalize(self,s1,s2):
        sq=self.convertData(s1)
        cursor.execute("""UPDATE DS SET barcode=%s,is_finish=%s, photo_final=%s WHERE Id=%s""",(self.barcode,1,sq,s2))
        connect.commit()
        cursor.execute("SELECT *FROM TelegramBots WHERE UserName=%s",(self.datas["user_name"]))
        data=cursor.fetchone()
        if data!=None:
            req="https://api.telegram.org/bot{0}/sendDocument".format(data["Api"])
            answer=requests.post(url=req,
                         data={
                             'chat_id': data["Chat"],
                             'document': 'attach://file',
                             'caption':'Ваша заявка по форме DS-160 под номером '+s2+' успешно зарегистрирована.\nБаркод заявки для записи на собеседование Вы можете найти в приложенной анкете.',
                         },
                         files={
                             'file': open(s1, 'rb'),
                         }
                      )


    def SetSelect(self,s1,s2):
        select = Select(self.driver.find_element(By.ID,s1))
        select.select_by_value(s2)

    def SetFinalQuestions(self,val1,id1,id2,id3,val2):
        try:
            if val1=="Да":
                self.driver.execute_script("""document.getElementById('"""+id1+"""').click();""")
                time.sleep(1.5)
                self.driver.execute_script("""document.getElementById('"""+id3+"""').value='"""+val2+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('"""+id2+"""').click();""")
                time.sleep(1.5)
        except Exception:
            pass
        #pass

    #def SetBarcode(self,check):
    #    cursor.execute("""UPDATE DS SET barcode=%s WHERE Id=%s""", (check,self.datas["Id"]))
    #    connect.commit()
        
    def Page1(self):
        try:
            sq=self.GenerateData(self.datas["part1"])
            self.driver.get("https://ceac.state.gov/GenNIV/Default.aspx")
            self.SetSelect('ctl00_SiteContentPlaceHolder_ucLocation_ddlLocation',sq[1])
            time.sleep(5)
            self.driver.save_screenshot('D:/'+str(self.objectname).strip()+'.png')
            img = Image.open('D:/'+str(self.objectname).strip()+'.png')
            w, h = img.size
            cropped_img = img.crop((330, 380, w-1250, h-500)).save('D:/'+str(self.objectname).strip()+'.png')
            check=self.CaptchaPage()
            if check[0]=="":
                os.remove('D:/'+str(self.objectname).strip()+'.png')  
                self.driver.execute_script("""document.getElementById("ctl00_SiteContentPlaceHolder_ucLocation_IdentifyCaptcha1_txtCodeTextBox").value='"""+check[1]+"""';""")
                self.driver.execute_script("""document.getElementById("ctl00_SiteContentPlaceHolder_lnkNew").click();""")            
                time.sleep(2)
                self.Page2()        
            else:
                self.Page1()
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page1()

    def Page2(self):
        try:
            time.sleep(5)
            bs=BeautifulSoup(self.driver.page_source,"lxml").findAll("input",{"id":"ctl00_SiteContentPlaceHolder_chkbxPrivacyAct"})
            sq=self.GenerateData(self.datas["part1"])
            if len(bs)==0:
                self.Page1()
            self.driver.execute_script("document.getElementById('ctl00_SiteContentPlaceHolder_chkbxPrivacyAct').click();")
            self.SetSelect('ctl00_SiteContentPlaceHolder_ddlQuestions',sq[3])
            time.sleep(5)
        
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_txtAnswer').value='"""+self.GenerateData(self.datas["part1"])[4]+"""';""")        
            val=str(BeautifulSoup(self.driver.page_source,"lxml").findAll("span",attrs={"id":'ctl00_SiteContentPlaceHolder_lblBarcode'})[0].text).strip()
            self.barcode=val
            #self.SetBarcode(val)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page2()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_btnContinue').click();""")     
        self.Page3()
        


    def Page3(self):
        try:
            sq=self.GenerateData(self.datas["part2"])
            time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SURNAME').value='"""+sq[0]+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_GIVEN_NAME').value='"""+sq[1]+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_FULL_NAME_NATIVE').value='"""+sq[2]+"""';""")  
            if str(sq[3])=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblOtherNames_0').click();""")
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_DListAlias_ctl00_tbxSURNAME').value='"""+str(sq[4])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_DListAlias_ctl00_tbxGIVEN_NAME').value='"""+str(sq[5])+"""';""")      
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblOtherNames_1').click();""")
            
            if str(sq[6])=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblTelecodeQuestion_0').click();""")
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_TelecodeSURNAME').value='"""+str(sq[7])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_TelecodeGIVEN_NAME').value='"""+str(sq[8])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblTelecodeQuestion_1').click();""")
        
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_GENDER',sq[10])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_MARITAL_STATUS',sq[12])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlDOBDay',sq[14])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlDOBMonth',sq[16])
       
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear').value='"""+str(sq[18])+"""';""")      

            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_POB_CITY').value='"""+str(sq[19])+"""';""")      
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_POB_ST_PROVINCE').value='"""+str(sq[20])+"""';""")    
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_POB_CNTRY',sq[22])
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page3()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page4()

    def Page4(self):
        try:
            sq=self.GenerateData(self.datas["part3"])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_NATL',sq[1])    
            if str(sq[2])=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAPP_OTH_NATL_IND_0').click();""")
                time.sleep(4)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_ddlOTHER_NATL',sq[4])
                if str(sq[5])=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_rblOTHER_PPT_IND_0').click();""")
                    time.sleep(2)
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_tbxOTHER_PPT_NUM').value='"""+str(sq[6])+"""';""")
                else:
                    self.driver.execute_script("document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_rblOTHER_PPT_IND_1').click();")     
                    time.sleep(2)
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAPP_OTH_NATL_IND_1').click();""")
                time.sleep(2)
            if str(sq[7])=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPermResOtherCntryInd_0').click();""")
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlOthPermResCntry_ctl00_ddlOthPermResCntry',sq[9])
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPermResOtherCntryInd_1').click();""")
                time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_NATIONAL_ID').value='"""+str(sq[10])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SSN1').value='"""+str(sq[11])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SSN2').value='"""+str(sq[12])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SSN3').value='"""+str(sq[13])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_TAX_ID').value='"""+str(sq[14])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page4()
        self.Page5()


    def Page5(self):
        try:
            sq=self.GenerateData(self.datas["part4"])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dlPrincipalAppTravel_ctl00_ddlPurposeOfTrip',sq[1])
            time.sleep(2)
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dlPrincipalAppTravel_ctl00_ddlOtherPurpose',sq[3])
            if sq[4]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblSpecificTravel_0').click();""")
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlARRIVAL_US_DTEDay',sq[6])
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlARRIVAL_US_DTEMonth',sq[8])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxARRIVAL_US_DTEYear').value='"""+str(sq[10])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxArriveFlight').value='"""+str(sq[11])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxArriveCity').value='"""+str(sq[12])+"""';""") 
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlDEPARTURE_US_DTEDay',sq[14])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlDEPARTURE_US_DTEMonth',sq[16])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxDEPARTURE_US_DTEYear').value='"""+str(sq[18])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxDepartFlight').value='"""+str(sq[19])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxDepartCity').value='"""+str(sq[20])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlTravelLoc_ctl00_tbxSPECTRAVEL_LOCATION').value='"""+str(sq[21])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxStreetAddress1').value='"""+str(sq[22])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxStreetAddress2').value='"""+str(sq[23])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxCity').value='"""+str(sq[24])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlTravelState',sq[26])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbZIPCode').value='"""+str(sq[27])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblSpecificTravel_1').click();""")
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlTRAVEL_DTEDay',sq[29])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlTRAVEL_DTEMonth',sq[31])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxTRAVEL_DTEYear').value='"""+str(sq[33])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxTRAVEL_LOS').value='"""+str(sq[34])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlTRAVEL_LOS_CD',sq[36])
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxStreetAddress1').value='"""+str(sq[37])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxStreetAddress2').value='"""+str(sq[38])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxCity').value='"""+str(sq[39])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlTravelState',sq[41])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbZIPCode').value='"""+str(sq[42])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlWhoIsPaying',sq[44])   
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page5()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page6()

    def Page6(self):
        try:
            sq=self.GenerateData(self.datas["part5"])
            if sq[0]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblOtherPersonsTravelingWithYou_0').click();""") 
                time.sleep(2)
                if sq[1]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblGroupTravel_0').click();""") 
                    time.sleep(2)
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxGroupName').value='"""+str(sq[2])+"""';""")
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblGroupTravel_1').click();""") 
                    time.sleep(2)
                    self.driver.execute_script("""document.getElementById('ctl00$SiteContentPlaceHolder$FormView1$dlTravelCompanions$ctl00$tbxSurname').value='"""+str(sq[3])+"""';""")
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dlTravelCompanions_ctl00_tbxGivenName').value='"""+str(sq[4])+"""';""")
                    self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dlTravelCompanions_ctl00_ddlTCRelationship',sq[6])
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblOtherPersonsTravelingWithYou_1').click();""")
                time.sleep(2)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page6()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")  
        self.Page7()


    def Page7(self):
        try:
            sq=self.GenerateData(self.datas["part6"])
            if sq[0]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_TRAVEL_IND_0').click();""") 
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_ctl00_ddlPREV_US_VISIT_DTEDay',sq[2]) 
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_ctl00_ddlPREV_US_VISIT_DTEMonth',sq[4]) 
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_ctl00_tbxPREV_US_VISIT_DTEYear').value='"""+str(sq[6])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_ctl00_tbxPREV_US_VISIT_LOS').value='"""+str(sq[7])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_ctl00_ddlPREV_US_VISIT_LOS_CD',sq[9]) 
                if sq[10]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_DRIVER_LIC_IND_0').click();""")
                    time.sleep(2)
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlUS_DRIVER_LICENSE_ctl00_tbxUS_DRIVER_LICENSE').value='"""+str(sq[11])+"""';""")
                    self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlUS_DRIVER_LICENSE_ctl00_ddlUS_DRIVER_LICENSE_STATE',sq[13])
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_DRIVER_LIC_IND_1').click();""")
                    time.sleep(2)
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_TRAVEL_IND_1').click();""") 
                time.sleep(2)

            if sq[14]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_IND_0').click();""")
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPREV_VISA_ISSUED_DTEDay',sq[16])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPREV_VISA_ISSUED_DTEMonth',sq[18])
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_ISSUED_DTEYear').value='"""+str(sq[20])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_FOIL_NUMBER').value='"""+str(sq[21])+"""';""")
                if sq[22]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_TYPE_IND_0').click();""")
                    time.sleep(2)
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_TYPE_IND_1').click();""")
                    time.sleep(2)
                if sq[23]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_CNTRY_IND_0').click();""")
                    time.sleep(2)
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_CNTRY_IND_1').click();""")
                    time.sleep(2)
                if sq[24]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_TEN_PRINT_IND_0').click();""")
                    time.sleep(2)
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_TEN_PRINT_IND_1').click();""")
                    time.sleep(2)
                if sq[25]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_LOST_IND_0').click();""")
                    time.sleep(2)
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_LOST_YEAR').value='"""+str(sq[26])+"""';""")
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_LOST_EXPL').value='"""+str(sq[27])+"""';""")
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_LOST_IND_1').click();""")
                    time.sleep(2)
                if sq[28]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_CANCELLED_IND_0').click();""")
                    time.sleep(2)
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_CANCELLED_EXPL').value='"""+str(sq[29])+"""';""")
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_CANCELLED_IND_1').click();""")
                    time.sleep(2)
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_IND_1').click();""")
            if sq[30]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_REFUSED_IND_0').click();""")
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_REFUSED_EXPL').value='"""+str(sq[31])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_REFUSED_IND_1').click();""")
                time.sleep(2)
            try:
                if sq[32]=="Да":
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblVWP_DENIAL_IND_0').click();""")
                    time.sleep(2)
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxVWP_DENIAL_EXPL').value='"""+str(sq[33])+"""';""")
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblVWP_DENIAL_IND_1').click();""")
                    time.sleep(2)
            except Exception:
                pass
        
            if sq[34]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblIV_PETITION_IND_0').click();""")
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxIV_PETITION_EXPL').value='"""+str(sq[35])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblIV_PETITION_IND_1').click();""")
                time.sleep(2)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page7()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")  
        self.Page8()

    def Page8(self):
        try:
            sq=self.GenerateData(self.datas["part7"])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_LN1').value='"""+str(sq[0])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_LN2').value='"""+str(sq[1])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_CITY').value='"""+str(sq[2])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_STATE').value='"""+str(sq[3])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_POSTAL_CD').value='"""+str(sq[4])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlCountry',sq[6])
            if sq[7]=="Да":    
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblMailingAddrSame_0').click();""") 
                time.sleep(2)           
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblMailingAddrSame_1').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_LN1').value='"""+str(sq[8])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_LN2').value='"""+str(sq[9])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_CITY').value='"""+str(sq[10])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_STATE').value='"""+str(sq[11])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_POSTAL_CD').value='"""+str(sq[12])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_HOME_TEL').value='"""+str(sq[15])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_MOBILE_TEL').value='"""+str(sq[16])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_BUS_TEL').value='"""+str(sq[17])+"""';""")
            if sq[18]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAddPhone_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlAddPhone_ctl00_tbxAddPhoneInfo').value='"""+str(sq[19])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAddPhone_1').click();""") 
                time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_EMAIL_ADDR').value='"""+str(sq[20])+"""';""")
            if sq[21]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAddEmail_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlAddEmail_ctl00_tbxAddEmailInfo').value='"""+str(sq[22])+"""';""")            
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAddEmail_1').click();""") 
                time.sleep(2)
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlSocial_ctl00_ddlSocialMedia',sq[24])
            time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlSocial_ctl00_tbxSocialMediaIdent').value='"""+str(sq[25])+"""';""")
            if sq[26]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAddSocial_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlAddSocial_ctl00_tbxAddSocialPlat').value='"""+str(sq[27])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlAddSocial_ctl00_tbxAddSocialHand').value='"""+str(sq[28])+"""';""")                    
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblAddSocial_1').click();""") 
                time.sleep(2)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page8()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")  
        self.Page9()
        
    def Page9(self):
        try:
            sq=self.GenerateData(self.datas["part8"])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_TYPE',sq[1])
            time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_NUM').value='"""+str(sq[2])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_BOOK_NUM').value='"""+str(sq[3])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_CNTRY',sq[5])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUED_IN_CITY').value='"""+str(sq[6])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUED_IN_STATE').value='"""+str(sq[7])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_IN_CNTRY',sq[9])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_DTEDay',sq[11])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_DTEMonth',sq[13])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUEDYear').value='"""+str(sq[15])+"""';""")
            time.sleep(5)
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_EXPIRE_DTEDay',sq[17])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_EXPIRE_DTEMonth',sq[19])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_EXPIREYear').value='"""+str(sq[21])+"""';""")
            if sq[22]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblLOST_PPT_IND_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlLostPPT_ctl00_tbxLOST_PPT_NUM').value='"""+str(sq[23])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlLostPPT_ctl00_ddlLOST_PPT_NATL',sq[25])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlLostPPT_ctl00_tbxLOST_PPT_EXPL').value='"""+str(sq[26])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblLOST_PPT_IND_1').click();""") 
                time.sleep(2)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page9()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page10()

    def Page10(self):
        try:
            sq=self.GenerateData(self.datas["part9"])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_SURNAME').value='"""+str(sq[0])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_GIVEN_NAME').value='"""+str(sq[1])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ORGANIZATION').value='"""+str(sq[2])+"""';""")
            time.sleep(2)
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlUS_POC_REL_TO_APP',sq[4])
            time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_LN1').value='"""+str(sq[5])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_LN2').value='"""+str(sq[6])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_CITY').value='"""+str(sq[7])+"""';""")    
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlUS_POC_ADDR_STATE',sq[9])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_POSTAL_CD').value='"""+str(sq[10])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_HOME_TEL').value='"""+str(sq[11])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_EMAIL_ADDR').value='"""+str(sq[12])+"""';""")
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page10()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")  
        self.Page11()
        

    def Page11(self):
        #time.sleep(60000)
        try:
            sq=self.GenerateData(self.datas["part10"])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_SURNAME').value='"""+str(sq[0])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_GIVEN_NAME').value='"""+str(sq[1])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlFathersDOBDay',sq[3])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlFathersDOBMonth',sq[5])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxFathersDOBYear').value='"""+str(sq[7])+"""';""")
            if sq[8]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblFATHER_LIVE_IN_US_IND_0').click();""") 
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlFATHER_US_STATUS',sq[10])
            else:      
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblFATHER_LIVE_IN_US_IND_1').click();""") 
                time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_SURNAME').value='"""+str(sq[11])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_GIVEN_NAME').value='"""+str(sq[12])+"""';""")

            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlMothersDOBDay',sq[14])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlMothersDOBMonth',sq[16])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxMothersDOBYear').value='"""+str(sq[18])+"""';""")
        
            if sq[19]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblMOTHER_LIVE_IN_US_IND_0').click();""") 
                time.sleep(5)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlMOTHER_US_STATUS',sq[21])
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblMOTHER_LIVE_IN_US_IND_1').click();""") 
                time.sleep(2)
        
            if sq[22]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblUS_IMMED_RELATIVE_IND_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_ctl00_tbxUS_REL_SURNAME').value='"""+str(sq[23])+"""';""")        
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_ctl00_tbxUS_REL_GIVEN_NAME').value='"""+str(sq[24])+"""';""")
            
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_ctl00_ddlUS_REL_TYPE',sq[26])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_ctl00_ddlUS_REL_STATUS',sq[28])
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblUS_IMMED_RELATIVE_IND_1').click();""") 
                time.sleep(2)
                if sq[29]=="Да":       
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblUS_OTHER_RELATIVE_IND_0').click();""")
                    time.sleep(2)
                else:
                    self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblUS_OTHER_RELATIVE_IND_1').click();""")
                    time.sleep(2)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page11()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")    
        self.Page12()


    def Page12(self):
        try:
            sq=self.GenerateData(self.datas["part11"])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxSpouseSurname').value='"""+str(sq[0])+"""';""")        
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxSpouseGivenName').value='"""+str(sq[1])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlDOBDay',sq[3])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlDOBMonth',sq[5])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear').value='"""+str(sq[7])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlSpouseNatDropDownList',sq[9])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxSpousePOBCity').value='"""+str(sq[10])+"""';""")
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlSpousePOBCountry',sq[12])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlSpouseAddressType',sq[14])
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page12()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")    
        self.Page13()


    def Page13(self):
        try:
            sq=self.GenerateData(self.datas["part12"])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlPresentOccupation',sq[1])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchName').value='"""+str(sq[2])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchAddr1').value='"""+str(sq[3])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchAddr2').value='"""+str(sq[4])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchCity').value='"""+str(sq[5])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxWORK_EDUC_ADDR_STATE').value='"""+str(sq[6])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxWORK_EDUC_ADDR_POSTAL_CD').value='"""+str(sq[7])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxWORK_EDUC_TEL').value='"""+str(sq[8])+"""';""")
            time.sleep(4)
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlEmpSchCountry',sq[10])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlEmpDateFromDay',sq[12])
            self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_ddlEmpDateFromMonth',sq[14])
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxEmpDateFromYear').value='"""+str(sq[16])+"""';""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxCURR_MONTHLY_SALARY').value='"""+str(sq[17])+"""';""")        
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxDescribeDuties').value='"""+str(sq[18])+"""';""")
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page13()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page14()


    def Page14(self):
        try:
            sq=self.GenerateData(self.datas["part13"])
            if sq[0]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPreviouslyEmployed_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbEmployerName').value='"""+str(sq[1])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbEmployerStreetAddress1').value='"""+str(sq[2])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbEmployerStreetAddress2').value='"""+str(sq[3])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbEmployerCity').value='"""+str(sq[4])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbxPREV_EMPL_ADDR_STATE').value='"""+str(sq[5])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbxPREV_EMPL_ADDR_POSTAL_CD').value='"""+str(sq[6])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_DropDownList2',sq[8])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbEmployerPhone').value='"""+str(sq[9])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbJobTitle').value='"""+str(sq[10])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbSupervisorSurname').value='"""+str(sq[11])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbSupervisorGivenName').value='"""+str(sq[12])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_ddlEmpDateFromDay',sq[14])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_ddlEmpDateFromMonth',sq[16])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbxEmpDateFromYear').value='"""+str(sq[18])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_ddlEmpDateToDay',sq[20])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_ddlEmpDateToMonth',sq[22])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbxEmpDateToYear').value='"""+str(sq[24])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl00_tbDescribeDuties').value='"""+str(sq[25])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblPreviouslyEmployed_1').click();""") 
                time.sleep(2)
        
            if sq[26]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblOtherEduc_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxSchoolName').value='"""+str(sq[27])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxSchoolAddr1').value='"""+str(sq[28])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxSchoolAddr2').value='"""+str(sq[29])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxSchoolCity').value='"""+str(sq[30])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxEDUC_INST_ADDR_STATE').value='"""+str(sq[31])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxEDUC_INST_POSTAL_CD').value='"""+str(sq[32])+"""';""") 
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_ddlSchoolCountry',sq[34])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxSchoolCourseOfStudy').value='"""+str(sq[35])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_ddlSchoolFromDay',sq[37])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_ddlSchoolFromMonth',sq[39])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxSchoolFromYear').value='"""+str(sq[41])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_ddlSchoolToDay',sq[43])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_ddlSchoolToMonth',sq[45])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl00_tbxSchoolToYear').value='"""+str(sq[47])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblOtherEduc_1').click();""") 
                time.sleep(2)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page14()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")    
        self.Page15()
        

    def Page15(self):
        try:
            sq=self.GenerateData(self.datas["part14"])
            if sq[0]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxCLAN_TRIBE_NAME').value='"""+str(sq[1])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_1').click();""") 
                time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlLANGUAGES_ctl00_tbxLANGUAGE_NAME').value='"""+str(sq[2])+"""';""")
            if sq[3]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblCOUNTRIES_VISITED_IND_0').click();""") 
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlCountriesVisited_ctl00_ddlCOUNTRIES_VISITED',sq[5])
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblCOUNTRIES_VISITED_IND_1').click();""") 
                time.sleep(2)
            if sq[6]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlORGANIZATIONS_ctl00_tbxORGANIZATION_NAME').value='"""+str(sq[7])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_1').click();""") 
                time.sleep(2)
            if sq[8]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblTALIBAN_IND_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxTALIBAN_EXPL').value='"""+str(sq[9])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblTALIBAN_IND_1').click();""") 
                time.sleep(2)
            if sq[10]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxSPECIALIZED_SKILLS_EXPL').value='"""+str(sq[11])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_1').click();""") 
                time.sleep(2)
            if sq[12]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_0').click();""") 
                time.sleep(2)
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_CNTRY',sq[14])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_BRANCH').value='"""+str(sq[15])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_RANK').value='"""+str(sq[16])+"""';""")
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_SPECIALTY').value='"""+str(sq[17])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_FROMDay',sq[19])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_FROMMonth',sq[21])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_FROMYear').value='"""+str(sq[23])+"""';""")
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_TODay',sq[25])
                self.SetSelect('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_TOMonth',sq[27])
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_TOYear').value='"""+str(sq[29])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_1').click();""") 
                time.sleep(2)
            if sq[30]=="Да":
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_0').click();""") 
                time.sleep(2)
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_tbxINSURGENT_ORG_EXPL').value='"""+str(sq[31])+"""';""")
            else:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_1').click();""") 
                time.sleep(2)
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page15()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")    
        self.Page16()

    def Page16(self):
        try:
            sq=self.GenerateData(self.datas["part15"])
            self.SetFinalQuestions(sq[0],'ctl00_SiteContentPlaceHolder_FormView1_rblDisease_0','ctl00_SiteContentPlaceHolder_FormView1_rblDisease_1','ctl00_SiteContentPlaceHolder_FormView1_tbxDisease',sq[1])
            self.SetFinalQuestions(sq[2],'ctl00_SiteContentPlaceHolder_FormView1_rblDisorder_0','ctl00_SiteContentPlaceHolder_FormView1_rblDisorder_1','ctl00_SiteContentPlaceHolder_FormView1_tbxDisorder',sq[3])
            self.SetFinalQuestions(sq[4],'ctl00_SiteContentPlaceHolder_FormView1_rblDruguser_0','ctl00_SiteContentPlaceHolder_FormView1_rblDruguser_1','ctl00_SiteContentPlaceHolder_FormView1_tbxDruguser',sq[5])
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page16()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page17()

    def Page17(self):
        try:
            sq=self.GenerateData(self.datas["part16"])
            self.SetFinalQuestions(sq[0],'ctl00_SiteContentPlaceHolder_FormView1_rblArrested_0','ctl00_SiteContentPlaceHolder_FormView1_rblArrested_1','ctl00_SiteContentPlaceHolder_FormView1_tbxArrested',sq[1])
            self.SetFinalQuestions(sq[2],'ctl00_SiteContentPlaceHolder_FormView1_rblControlledSubstances_0','ctl00_SiteContentPlaceHolder_FormView1_rblControlledSubstances_1','ctl00_SiteContentPlaceHolder_FormView1_tbxControlledSubstances',sq[3])
            self.SetFinalQuestions(sq[4],'ctl00_SiteContentPlaceHolder_FormView1_rblProstitution_0','ctl00_SiteContentPlaceHolder_FormView1_rblProstitution_1','ctl00_SiteContentPlaceHolder_FormView1_tbxProstitution',sq[5])
            self.SetFinalQuestions(sq[6],'ctl00_SiteContentPlaceHolder_FormView1_rblMoneyLaundering_0','ctl00_SiteContentPlaceHolder_FormView1_rblMoneyLaundering_1','ctl00_SiteContentPlaceHolder_FormView1_tbxMoneyLaundering',sq[7])
            self.SetFinalQuestions(sq[8],'ctl00_SiteContentPlaceHolder_FormView1_rblHumanTrafficking_0','ctl00_SiteContentPlaceHolder_FormView1_rblHumanTrafficking_1','ctl00_SiteContentPlaceHolder_FormView1_tbxHumanTrafficking',sq[9])
            self.SetFinalQuestions(sq[10],'ctl00_SiteContentPlaceHolder_FormView1_rblAssistedSevereTrafficking_0','ctl00_SiteContentPlaceHolder_FormView1_rblAssistedSevereTrafficking_1','ctl00_SiteContentPlaceHolder_FormView1_tbxAssistedSevereTrafficking',sq[11])
            self.SetFinalQuestions(sq[12],'ctl00_SiteContentPlaceHolder_FormView1_rblHumanTraffickingRelated_0','ctl00_SiteContentPlaceHolder_FormView1_rblHumanTraffickingRelated_1','ctl00_SiteContentPlaceHolder_FormView1_tbxHumanTraffickingRelated',sq[13])
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page17() 
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page18()
        
    def Page18(self):
        try:
            sq=self.GenerateData(self.datas["part17"])
            self.SetFinalQuestions(sq[0],'ctl00_SiteContentPlaceHolder_FormView1_rblIllegalActivity_0','ctl00_SiteContentPlaceHolder_FormView1_rblIllegalActivity_1','ctl00_SiteContentPlaceHolder_FormView1_tbxIllegalActivity',sq[1])
            self.SetFinalQuestions(sq[2],'ctl00_SiteContentPlaceHolder_FormView1_rblTerroristActivity_0','ctl00_SiteContentPlaceHolder_FormView1_rblTerroristActivity_1','ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristActivity',sq[3])
            self.SetFinalQuestions(sq[4],'ctl00_SiteContentPlaceHolder_FormView1_rblTerroristSupport_0','ctl00_SiteContentPlaceHolder_FormView1_rblTerroristSupport_1','ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristSupport',sq[5])
            self.SetFinalQuestions(sq[6],'ctl00_SiteContentPlaceHolder_FormView1_rblTerroristOrg_0','ctl00_SiteContentPlaceHolder_FormView1_rblTerroristOrg_1','ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristOrg',sq[7])
            self.SetFinalQuestions(sq[8],'ctl00_SiteContentPlaceHolder_FormView1_rblTerroristRel_0','ctl00_SiteContentPlaceHolder_FormView1_rblTerroristRel_1','ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristRel',sq[9])
            self.SetFinalQuestions(sq[10],'ctl00_SiteContentPlaceHolder_FormView1_rblGenocide_0','ctl00_SiteContentPlaceHolder_FormView1_rblGenocide_1','ctl00_SiteContentPlaceHolder_FormView1_tbxGenocide',sq[11])
            self.SetFinalQuestions(sq[12],'ctl00_SiteContentPlaceHolder_FormView1_rblTorture_0','ctl00_SiteContentPlaceHolder_FormView1_rblTorture_1','ctl00_SiteContentPlaceHolder_FormView1_tbxTorture',sq[13])
            self.SetFinalQuestions(sq[14],'ctl00_SiteContentPlaceHolder_FormView1_rblExViolence_0','ctl00_SiteContentPlaceHolder_FormView1_rblExViolence_1','ctl00_SiteContentPlaceHolder_FormView1_tbxExViolence',sq[15])
            self.SetFinalQuestions(sq[16],'ctl00_SiteContentPlaceHolder_FormView1_rblChildSoldier_0','ctl00_SiteContentPlaceHolder_FormView1_rblChildSoldier_1','ctl00_SiteContentPlaceHolder_FormView1_tbxChildSoldier',sq[17])
            self.SetFinalQuestions(sq[18],'ctl00_SiteContentPlaceHolder_FormView1_rblReligiousFreedom_0','ctl00_SiteContentPlaceHolder_FormView1_rblReligiousFreedom_1','ctl00_SiteContentPlaceHolder_FormView1_tbxReligiousFreedom',sq[19])
            self.SetFinalQuestions(sq[20],'ctl00_SiteContentPlaceHolder_FormView1_rblPopulationControls_0','ctl00_SiteContentPlaceHolder_FormView1_rblPopulationControls_1','ctl00_SiteContentPlaceHolder_FormView1_tbxPopulationControls',sq[21])
            self.SetFinalQuestions(sq[22],'ctl00_SiteContentPlaceHolder_FormView1_rblTransplant_0','ctl00_SiteContentPlaceHolder_FormView1_rblTransplant_1','ctl00_SiteContentPlaceHolder_FormView1_tbxTransplant',sq[23])
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page18()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page19()
        
        
    def Page19(self):
        try:
            sq=self.GenerateData(self.datas["part18"])
            self.SetFinalQuestions(sq[0],'ctl00_SiteContentPlaceHolder_FormView1_rblRemovalHearing_0','ctl00_SiteContentPlaceHolder_FormView1_rblRemovalHearing_1','ctl00_SiteContentPlaceHolder_FormView1_tbxRemovalHearing',sq[1])
            self.SetFinalQuestions(sq[2],'ctl00_SiteContentPlaceHolder_FormView1_rblImmigrationFraud_0','ctl00_SiteContentPlaceHolder_FormView1_rblImmigrationFraud_1','ctl00_SiteContentPlaceHolder_FormView1_tbxImmigrationFraud',sq[3])
            self.SetFinalQuestions(sq[4],'ctl00_SiteContentPlaceHolder_FormView1_rblFailToAttend_0','ctl00_SiteContentPlaceHolder_FormView1_rblFailToAttend_1','ctl00_SiteContentPlaceHolder_FormView1_tbxFailToAttend',sq[5])
            self.SetFinalQuestions(sq[6],'ctl00_SiteContentPlaceHolder_FormView1_rblVisaViolation_0','ctl00_SiteContentPlaceHolder_FormView1_rblVisaViolation_1','ctl00_SiteContentPlaceHolder_FormView1_tbxVisaViolation',sq[7])
            self.SetFinalQuestions(sq[8],'ctl00_SiteContentPlaceHolder_FormView1_rblDeport_0','ctl00_SiteContentPlaceHolder_FormView1_rblDeport_1','ctl00_SiteContentPlaceHolder_FormView1_tbxDeport_EXPL',sq[9])
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page19()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page20()
        
    def Page20(self):
        try:
            sq=self.GenerateData(self.datas["part19"])
            self.SetFinalQuestions(sq[0],'ctl00_SiteContentPlaceHolder_FormView1_rblChildCustody_0','ctl00_SiteContentPlaceHolder_FormView1_rblChildCustody_1','ctl00_SiteContentPlaceHolder_FormView1_tbxChildCustody',sq[1])
            self.SetFinalQuestions(sq[2],'ctl00_SiteContentPlaceHolder_FormView1_rblVotingViolation_0','ctl00_SiteContentPlaceHolder_FormView1_rblVotingViolation_1','ctl00_SiteContentPlaceHolder_FormView1_tbxVotingViolation',sq[3])
            self.SetFinalQuestions(sq[4],'ctl00_SiteContentPlaceHolder_FormView1_rblRenounceExp_0','ctl00_SiteContentPlaceHolder_FormView1_rblRenounceExp_1','ctl00_SiteContentPlaceHolder_FormView1_tbxRenounceExp',sq[5])
            self.SetFinalQuestions(sq[6],'ctl00_SiteContentPlaceHolder_FormView1_rblAttWoReimb_0','ctl00_SiteContentPlaceHolder_FormView1_rblAttWoReimb_1','ctl00_SiteContentPlaceHolder_FormView1_tbxAttWoReimb',sq[7])
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page20()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page21()
        

    def Page21(self):
        try:
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_btnUploadPhoto').click();""") 
            sq=bytearray(self.datas["photo"])
            with open('D:/'+str(self.objectname).strip()+'_photo.jpg', 'wb') as output:
                output.write(sq)
            time.sleep(2)
            self.driver.find_element(By.ID,"ctl00_cphMain_imageFileUpload").send_keys('D:/'+str(self.objectname).strip()+'_photo.jpg')
            self.driver.execute_script("""document.getElementById('ctl00_cphButtons_btnUpload').click();""")
            time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_cphButtons_btnNoImage').click();""")
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page21()
        self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        self.Page22()

    def Page22(self):
        try:
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton2').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_btnContinueApp').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page22()
        self.Page23()

    def Page23(self):
        try:
            passp=self.GenerateData(self.datas["part8"])
            self.driver.execute_script("""window.scrollTo(0, document.body.scrollHeight);""")
            time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_FormView3_rblPREP_IND_1').click();""")
            time.sleep(2)
            self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_PPTNumTbx').value='"""+str(passp[2])+"""';""")
            time.sleep(2)
            self.driver.execute_script("""window.scrollTo(0, document.body.scrollHeight);""")
            time.sleep(2)
            self.driver.save_screenshot('D:/'+str(self.objectname).strip()+'.png')
            img = Image.open('D:/'+str(self.objectname).strip()+'.png')
            w, h = img.size
            cropped_img = img.crop((390, 520, w-1250, h-340)).save('D:/'+str(self.objectname).strip()+'.png')
            check=self.CaptchaPage()
            if check[0]=="":
                os.remove('D:/'+str(self.objectname).strip()+'.png')#check[1]
                self.driver.execute_script("""document.getElementById("ctl00_SiteContentPlaceHolder_CodeTextBox").value='"""+check[1]+"""';""")
                self.driver.execute_script("""document.getElementById("ctl00_SiteContentPlaceHolder_btnSignApp").click();""")            
                self.Page24()
            else:
                self.Page23()
        except Exception:
            self.driver.execute_script("window.location.reload();")
            self.Page23()

    def Page24(self):
        bs=str(BeautifulSoup(self.driver.page_source,"lxml").findAll("div",{"class":"error-message"})[0].get("style"))
        if bs=="color:Red;background-color:White;":
            self.Page23()
        else:
            try:
                self.driver.execute_script("""document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3').click();""")
                self.driver.save_screenshot('D:/'+str(self.objectname).strip()+'_FINAL.png')
                img = Image.open('D:/'+str(self.objectname).strip()+'_FINAL.png')
                w, h = img.size
                cropped_img = img.crop((10, 100, w-1200, h-400)).save('D:/'+str(self.objectname).strip()+'_FINAL.png')
                self.SetFinalize('D:/'+str(self.objectname).strip()+'_FINAL.png',self.datas["Id"])
                #image_1 = Image.open('D:/'+str(self.objectname).strip()+'_FINAL.png')
                #im_1 = image_1.convert('RGB')
                #im_1.save('D:/'+str(self.objectname).strip()+'_FINAL.pdf')
                os.remove('D:/'+str(self.objectname).strip()+'_FINAL.png')
                time.sleep(5)
                self.driver.close()
                self.driver.quit()
            except Exception:
                self.driver.execute_script("window.location.reload();")
                self.Page24()

    def startSelenium(self,objectn):
        self.objectname=objectn
        self.datas=self.GetData(self.datas)
        self.driver = uc.Chrome()
        self.driver.maximize_window()
        self.Page1()




#782fcf78-6422-4591-8a99-114900cec405

#k=StartDSRecord("935b1270-9d43-4ff8-8827-0fdb04d7d0a0")
#k=StartDSRecord("adfad002-c20e-425d-96f7-3863e0dc9e70")
#k.startSelenium(str(k).split("at 0x")[1].replace(">","").strip())
def startsds(datas):
    k=StartDSRecord(datas["datadsid"])   
    k.startSelenium(str(k).split("at 0x")[1].replace(">","").strip())

THREAD1=None
app = Flask(__name__)
CORS(app)

@app.route('/setdatads', methods=['POST'])
def startdata():
    THREAD1 = threading.Thread(target=startsds,args=(request.json,), daemon=True)
    THREAD1.start()
    return "OKDS"

if __name__ == '__main__':
    app.run()