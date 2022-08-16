import urllib.parse
import logging
import zipfile
from io import BytesIO
from boto3 import resource

print('Loading function')
s3_resource = resource('s3')
UNZIPPED_FOLDER = "facturas/"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def unzip_and_gzip_files(filekey, sourcebucketname):
    try:
        zipped_file = s3_resource.Object(bucket_name=sourcebucketname, key=filekey)
        buffer = BytesIO(zipped_file.get()["Body"].read())
        zipped = zipfile.ZipFile(buffer)
        s3_bucket_resource = s3_resource.Bucket(sourcebucketname)
        
        for file in zipped.namelist():
            logger.info(f'current file in zipfile: {file}')
            final_file_path = UNZIPPED_FOLDER + file

            with zipped.open(file, "r") as f_in:
                gzipped_content = f_in.read()
                s3_bucket_resource.upload_fileobj(BytesIO(gzipped_content),
                                                        final_file_path,
                                                        ExtraArgs={"ContentType": "text/plain"}
                                                )
    except Exception as e:  
        logger.info(f'Error: Unable to unzip & upload file: {e}')


def lambda_handler(event, context):

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    logger.info(f'current file to unzip: {key}')
    unzip_and_gzip_files(key, bucket)
    
    return {
        'statusCode': 200
    }
