#!usr/bin/python

# sensor de movimento
from gpiozero import MotionSensor
from gpiozero import LED

# camera
from picamera import PiCamera
from time import sleep

# aws
import boto3

pir = MotionSensor(pin=25) # variavel do sensor de movimento

while(True):
    if(pir.motion_detected):
        camera = PiCamera()
        camera.start_preview()
        sleep(5)
        camera.capture('/home/pi/Desktop/image.jpg') # local para salvar a imagem
        camera.stop_preview()

        session = boto3.Session(
	    aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,
	    aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY, 
	    region_name=REGION_NAME
	)
        s3 = session.resource('s3') # variavel s3 da aws
        filename = 'image.jpg' # pegar caminho da iamgem tirada pela camera do rasp
        bucket_name = 'my-bucket' # nome do bucket no S3

        # Upload 
        s3.upload_file(filename, bucket_name, filename)

BUCKET = "amazon-rekognition" # nome do bucket na aws
KEY_SOURCE = "test.jpg" # imagem que vai usar de exemplo para comparção
KEY_TARGET = "target.jpg" # imagem que o raspbery vai tirar

def compare_faces(bucket, key, bucket_target, key_target, threshold=80, region="eu-west-1"): # trocar region
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
print "Source Face ({Confidence}%)".format(**source_face)

for match in matches:
	print "Target Face ({Confidence}%)".format(**match['Face'])
	print "  Similarity : {}%".format(match['Similarity'])

    if(match['Similarity'] < 90%): # ajustar número ideal
        # enviar mensagem mqtt (ou qualquer outra), contendo a imagem capturada
        # No app, receber a imagem e dar opções de ações (disparar busina, ligar para policia, não fazer nada)

"""
    Expected output:
    Source Face (99.945602417%)
    Target Face (99.9963378906%)
      Similarity : 89.0%
"""
