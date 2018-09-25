#!usr/bin/python

# sensor de distancia
import RPi.GPIO as GPIO    #Importamos a libraria GPIO
import time                #Importamos time (time.sleep)

# camera
from picamera import PiCamera
from time import sleep

# aws
import boto3

# mqtt
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BCM)     #Colocamos a placa em modo BCM
GPIO_TRIGGER = 25          #Usamos o pin GPIO 25 como TRIGGER
GPIO_ECHO    = 7           #Usamos o pin GPIO 7 como ECHO
GPIO.setup(GPIO_TRIGGER,GPIO.OUT)  #Configuramos Trigger como saída
GPIO.setup(4,GPIO.OUT)  #Configuramos Trigger como saída
GPIO.setup(GPIO_ECHO,GPIO.IN)      #Configuramos Echo como entrada
GPIO.output(GPIO_TRIGGER,False)    #Colocamos o pin 25 como LOW

while(True):
	GPIO.output(GPIO_TRIGGER,True)   #Enviamos uma pressão de ultrasonidos
	time.sleep(0.00001)              #Uma pequena pausa
	GPIO.output(GPIO_TRIGGER,False)  #Apagamos a pressão
	start = time.time()              #Guarda o tempo atual mediante time.time()
	while GPIO.input(GPIO_ECHO)==0:  #Enquanto o sensor não receba sinal...
		start = time.time()          #Mantemos o tempo actual mediante time.time()
	while GPIO.input(GPIO_ECHO)==1:  #Se o sensor recebe sinal...
		stop = time.time()           #Guarda o tempo actual mediante time.time() noutra variavel
	elapsed = stop-start             #Obtemos o tempo decorrido entre envío y receção
	distance = (elapsed * 34300)/2   #Distancia é igual ao tempo por velocidade partido por 2   D = (T x V)/2
	print (distance)                   #Devolvemos a distancia (em centímetros) por ecrã
	time.sleep(1)                    #Pequena pausa para não saturar o procesador do Raspberry
	
	SESSION = session = boto3.Session(
			aws_access_key_id="ACCESS_KEY",
			aws_secret_access_key="SECRET_KEY", 
			region_name="us-east-1"
		)
	
	if(distance < 500):
		camera = PiCamera()
		camera.start_preview()
		sleep(5)
		camera.capture('/home/pi/Desktop/image.jpg') # local para salvar a imagem
		camera.stop_preview()
		
		
		s3 = session.resource('s3').Bucket('recognition-example')
		filename = 'image.jpg' # pegar caminho da iamgem tirada pela camera do rasp
		bucket_name = 'recognition-example' # nome do bucket no S3
		
		s3.upload_file('/home/pi/Desktop/image.jpg', filename)
		
		BUCKET = "recognition-example" # nome do bucket na aws
		KEY_SOURCE = 'test.jpg' # imagem que vai usar de exemplo para comparação
		KEY_TARGET = "image.jpg" # imagem que o raspbery vai tirar
		
		def compare_faces(bucket, key, bucket_target, key_target, session, threshold=80, region="us-east-1"): # trocar region
			rekognition = session.client("rekognition", region)
			
			source_bytes = open('/home/pi/Desktop/test.jpg', 'rb')
			target_bytes = open('/home/pi/Desktop/image.jpg', 'rb')
			
			response = rekognition.compare_faces(
				SourceImage={
					'Bytes':source_bytes.read()
				},
				TargetImage={
					'Bytes':target_bytes.read()
				},
				SimilarityThreshold=threshold,
			)
			return response['SourceImageFace'], response['FaceMatches']

		source_face, matches = compare_faces(BUCKET, KEY_SOURCE, BUCKET, KEY_TARGET, SESSION)

		for match in matches:
			print ("  Similarity : {}%".format(match['Similarity']))
			client = mqtt.Client("P1")
			client.connect("broker.hivemq.com", 1883, 60)
			client.publish("iot/test","enviar imagem")
			#if(match['Similarity'] < 90%):
				
				# enviar mensagem mqtt (ou qualquer outra), contendo a imagem capturada
				# No app, receber a imagem e dar opções de ações (disparar busina, ligar para policia, não fazer nada)
		sleep(100)
	else:
		GPIO.output(4,False)
