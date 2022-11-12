from src.types.types import Localconfig
import os

localconfig = Localconfig(host=os.environ['DB_HOST'],
                          user=os.environ['DB_USER'],
                          password=os.environ['DB_PASSWORD'],
                          db=os.environ['DB_NAME'])