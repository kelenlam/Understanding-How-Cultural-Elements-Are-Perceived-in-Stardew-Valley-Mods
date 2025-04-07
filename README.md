# Setup

1.Install Python 3.10.11 https://www.python.org/downloads/release/python-31011/ 

2.Download final.zip from Git Hub and extract it. 

3.Install MongoDB compass https://www.mongodb.com/try/download/community During installation, set up final/mongodb_data and final/mongodb_log as MongoDB data and log directories. 

4.Install Windows Subsystem for Linux (WSL) https://learn.microsoft.com/en-us/windows/wsl/install 

5.Install Redis in WSL https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-windows/ 

6.Setup Windows firewall to allow incoming and outgoing port 27017 for MongoDB and port 6379 for Redis. 

7.Setup ufw in WSL to allow incoming and outgoing port 6379. (1. sudo apt install ufw 2. sudo ufw enable 3. sudo ufw allow in 6379 4. sudo ufw allow out 6379) 

8.If the Chrome version is not compatible with Chrome driver 134.0.6998.165, download the latest Chrome driver and replace chromedriver.exe in the final. https://googlechromelabs.github.io/chrome-for-testing/ 

9.In final folder, run: python setup.py 

10.According to the instructions printed after running setup.py, activate the virtual environment and set the path. 



# Demo

1.Start MongoDB with administrator privilege cmd, run: net start MongoDB 

2.Start Redis with cmd, run: 1. wsl 2.sudo service redis-server start 

3.In final folder, activate the virtual environment, then run: uvicorn backend.main:app --reload
