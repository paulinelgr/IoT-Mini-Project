#Projet IoT - M1S2
#Groupe 5 : Essedik EL ABDELLAOUI, Pauline LEGER, Marie ROELANDTS, Anass HMIMOU

#Imports
import time
from grovepi import *
from grove_rgb_lcd import *
import sys
import json

#Determine les pins de chaque entrée/sortie
capteur_th = 7
ecran = 2
bar_led = 2
capteur_eau = 3
capteur_gaz = 2
bouton = 4
buzzer = 8
servo = 5
led = 6

pinMode(servo,"OUTPUT")
pinMode(capteur_th,"INPUT")
pinMode(ecran,"OUTPUT")
pinMode(bar_led,"OUTPUT")
pinMode(capteur_eau,"INPUT")
pinMode(capteur_gaz,"INPUT")
pinMode(bouton,"INPUT")
pinMode(buzzer,"OUTPUT")
pinMode(servo,"OUTPUT")
pinMode(led,"OUTPUT")

#Etablissement de la boucle de gestion de messsages 
import paho.mqtt.client as mqtt
import time

def on_connect(client,userdata,flags,result):
     try:
          if (result==0):
               client.subscribe("/junia/#",2)
          else:
               print("erreur de connexion")
               quit(0)
     except Exception as e:
          print(e)
          quit(0)

def on_message(client,userdata,message):
     try:
          print("Received message '" + message.payload.decode("utf8") 
          + "' on topic '" + message.topic 
          + "' with Qos " + str(message.qos))
          if(message.payload.decode("utf8") == "oui"):  #Enclenche l'ouverture de porte si envoie du message oui
              print("OK")
              analogWrite(servo,180)
              time.sleep(1)
              analogWrite(servo,0)
          elif(message.payload.decode("utf8") == "Allumer led"):   #Allume la led si message correspondant
              digitalWrite(led,1)
          elif(message.payload.decode("utf8") == "Eteindre led") :   #Eteint la led si message correspondant
              digitalWrite(led,0)

     except Exception as e:
          print(e)

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("test.mosquitto.org", 1883, 60)   #Connexion à test.mosquitto.org, port 1883
 
mqttc.loop_start()


while True:
     try:
          #Capteur d'humidité/température 
          [t, h]=dht(capteur_th,0)

          setRGB(0,255,0)
          time.sleep(1)
          setText_norefresh("Temp:"+str(t)+"C\n"+"Humidity:"+str(h)+"%")   #Affichage des valeurs d'humidite/temp sur l'ecran LCD
          ledBar_init(bar_led,1)  #Initialisatoin de la barre LED, inversée afin d'allumer le level rouge quand supérieur à 35
          if (t<10):
                ledBar_setLevel(bar_led, 1)
          elif (10<t<15):
                ledBar_setLevel(bar_led, 2)
          elif (15<t<20):
                ledBar_setLevel(bar_led, 3)
          elif (20<t<25):
                ledBar_setLevel(bar_led, 4)
          elif (25<t<30):
                ledBar_setLevel(bar_led, 5)
          elif (30<t<32):
                ledBar_setLevel(bar_led, 6)
          elif (32<t<35):
                ledBar_setLevel(bar_led, 7)
          elif (t>35):
                ledBar_setLevel(bar_led, 8)

          donnees={"temperature":t,"humidite":h}
          donnees_json=json.dumps(donnees)  #Passage des données au format json
          print(donnees_json)
          mqttc.publish("temp_hum",donnees_json,2)  #Publication des données sur le topic temp_hum

          #Capteur d'eau
          niv_eau = digitalRead(capteur_eau)
          print(niv_eau)
          if (niv_eau == 0) :    #Message d'alerte si présence d'eau
                print("Alerte : Présence d'eau")
                mqttc.publish("eau","Alerte présence d'eau",2)   #Publication des données sur le topic eau 


          #Capteur de gaz
          niv_gaz = analogRead(capteur_gaz)
          print("Le niveau de gaz est",niv_gaz)
          if (niv_gaz > 5000):    #Message d'alerte si présence de gaz
               digitalWrite(buzzer,1)    #Mise en route du buzzer
               time.sleep(.5)
               digitalWrite(buzzer,0)
               mqttc.publish("gaz","Alerte niveau de gaz important!",2)   #Publication des données sur le topic gaz
          else :
               digitalWrite(buzzer,0)

          #Bouton
          val_bouton = digitalRead(bouton)
          phrase = "Il y a quelqu'un à la porte. Souhaitez-vous ouvrir?"
          if (val_bouton == 1):   #Si appuie sur le bouton (sonnerie), envoi d'un message d'alerte
               print("Il y a quelqu'un à la porte")
               mqttc.publish("porte",phrase,2)     #Publication des données sur le topic porte
          mqttc.subscribe("action",2)     #Souscription au topic action, qui permettra d'enclencher le servomoteur (ouverture de la porte)


          mqttc.subscribe("led",2)   #Souscription au topic led, qui permettra d'allumer la led

     except KeyboardInterrupt:  #Eteindre la led et buzzer avant l'arrêt
          digitalWrite(led,0)
          digitalWrite(buzzer,0)
          break

     except IOError:  #Afficher Error si erreur de communication rencontrée
          print("Error")
