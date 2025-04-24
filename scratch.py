import schedule
import time

def printr():
    # print("BIG")
    print("MAD")
    i=False

schedule.every(2).seconds.do(printr)

while True:
    i= True
    schedule.run_pending()
    time.sleep(1)
