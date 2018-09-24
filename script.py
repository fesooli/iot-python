#!usr/bin/python

# sensor de distancia
import RPi.GPIO as GPIO    #Importamos a libraria GPIO
import time                #Importamos time (time.sleep)

# camera
from picamera import PiCamera
from time import sleep

# aws
import boto3

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
	if(distance < 50):
		camera = PiCamera()
		camera.start_preview()
		#sleep(5)
		camera.capture('/home/pi/Desktop/image.jpg') # local para salvar a imagem
		camera.stop_preview()
		
		session = boto3.Session(
			aws_access_key_id="AKIAJXNAESFMTGWY37OA",
			aws_secret_access_key="mpwcuOUT20bjb+OHLqPyShCHatpwpxJPtiwcAqDe", 
			region_name="us-east-1"
		)
		s3 = session.resource('s3').Bucket('recognition-example')
		filename = 'image.jpg' # pegar caminho da iamgem tirada pela camera do rasp
		bucket_name = 'recognition-example' # nome do bucket no S3
		
		s3.upload_file('/home/pi/Desktop/image.jpg', filename)
	else:
		GPIO.output(4,False)

BUCKET = "amazon-rekognition" # nome do bucket na aws
KEY_SOURCE = "test.jpg" # imagem que vai usar de exemplo para comparação
KEY_TARGET = "target.jpg" # imagem que o raspbery vai tirar

def compare_faces(bucket, key, bucket_target, key_target, threshold=80, region="us-east-1"): # trocar region
	rekognition = boto3.client("rekognition", region)
	response = rekognition.compare_faces(
	    SourceImage={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		TargetImage={
			"S3Object": {
				"Bucket": bucket_target,
				"Name": key_target,
			}
		},
	    SimilarityThreshold=threshold,
	)
	return response['SourceImageFace'], response['FaceMatches']

source_face, matches = compare_faces(BUCKET, KEY_SOURCE, BUCKET, KEY_TARGET) # faz a request de compara de imagens

# faz o print de resultados...
"""

print "Source Face ({Confidence}%)".format(**source_face)

for match in matches:
	print "Target Face ({Confidence}%)".format(**match['Face'])
	print "  Similarity : {}%".format(match['Similarity'])

    if(match['Similarity'] < 90%): # ajustar número ideal
        # enviar mensagem mqtt (ou qualquer outra), contendo a imagem capturada
        # No app, receber a imagem e dar opções de ações (disparar busina, ligar para policia, não fazer nada)


    Expected output:
    Source Face (99.945602417%)
    Target Face (99.9963378906%)
      Similarity : 89.0%
"""
