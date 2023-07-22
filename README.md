# Chisel
# Scheduler and job clicking tool
## A basic web application to manage scheduled and interactive jobs easier

### Howto
* [ Requirements ]
- Python3
- Flask
- python-Crontab
- Flask-SQLALchemy
- requests

## Setup 

1. Install python3.9 if you don't have it

2. Clone this repository

3. Create a new virtual environment and activate it

    ```bash
    $ python3 -m venv chiselenv
    $ source chiselenv/bin/activate
    ```

4. Install the requirements

    ```bash
    $ pip install -r requirements.txt
    ```
5. Create Creds file as ~/.chisel/chisel.conf
 
    ```
    [GIT]
    GIT_PATH = ....
    ```
    - Please use the absolut PATH 
6. Run the application
    ```bash
    $ python3 app.py
    ```
    
