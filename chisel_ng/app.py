from flask import Flask , render_template ,request ,redirect ,url_for , flash
from flask_sqlalchemy import SQLAlchemy
from crontab import CronTab 
import os
import getpass
import subprocess

db = SQLAlchemy()
app = Flask(__name__ ,template_folder='templates')


#secret key generate with secrets.token_hex(16)
app.config['SECRET_KEY'] = 'ce4a6d224db8c3035970594aa95c36a6'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
db.init_app(app)

cron_user = getpass.getuser()


### Chisel Jobs Divider in Crontab 
### check if a divider exist, if not (that mean you are using chisel for the first Time)
### add a divider ,else just ignore

divider = str('###############  CHISEL JOBS  ###############')

def check_crontab_divider():
    result = subprocess.run(['crontab' , '-l'], stdout=subprocess.PIPE)
    lines = result.stdout.decode().split('\n')
    if divider in lines:
        return True
    return False

## this Methode will append save all crontab entry in param (lines) , then append divider in it 
## then copy lines in crontab again
def add_crontab_divider():
    if not check_crontab_divider():
        result =subprocess.run(['crontab' , '-l'], stdout=subprocess.PIPE)
        lines = result.stdout.decode().split('\n')
        lines.append('\n' + divider + '\n')
        new_crontab = '\n'.join(lines)
        p = subprocess.Popen('crontab' , stdin=subprocess.PIPE)
        p.communicate(input=new_crontab.encode())



class Cronjob(db.Model):
    id = db.Column(db.Integer, primary_key= True , autoincrement=True)
    status = db.Column(db.Boolean, nullable=False)
    desc = db.Column(db.String(500) , default=' ', nullable=True )
    minute = db.Column(db.String(50),default=' ', nullable=True)
    hour = db.Column(db.String(50), default=' ', nullable=True)
    day = db.Column(db.String(50), default=' ', nullable=True)
    month = db.Column(db.String(50), default=' ', nullable=True)
    dow = db.Column(db.String(50), default=' ', nullable=True)
    command = db.Column(db.String(500), nullable=False)

    def __repr__(self) -> str:
        return f"Cronjob('{self.minute}' , '{self.hour}' , '{self.day}' , '{self.month}' , '{self.dow}' , '{self.command}')" 

    def __init__(self, *args, **kwargs):
        if not kwargs.get('id'):
            kwargs['id'] = db.session.query(db.func.max(Cronjob.id)).scalar() + 1 if db.session.query(db.func.max(Cronjob.id)).scalar() else 1001
        super(Cronjob, self).__init__(*args, **kwargs)

    def add_to_tab(self):
        cron = CronTab(user=cron_user)
        job = cron.new(self.command)
        job.setall(self.minute , self.hour , self.day , self.month , self.dow)
        job.set_comment('Job-ID: ' +str(self.id) + " # | ## " + self.desc +" ##", pre_comment=True)
        if job.is_valid():
            cron.write()
            flash('Job added successfully' , "success")
        else:
            flash('Job invaild !!' , "failed")
    

    def update_in_tab(self , olddesc):
        cron = CronTab(user=cron_user)
        job = next(cron.find_comment('Job-ID: ' +str(self.id) + " # | ## " + olddesc +" ##"))
        job.set_command(self.command)
        job.setall(self.minute , self.hour , self.day , self.month , self.dow)
        job.set_comment('Job-ID: ' +str(self.id) + " # | ## " + self.desc +" ##", pre_comment=True)
        if job.is_valid():
            cron.write()
        else:
            flash('Job invaild !!' , "failed")
            return False
    

    def delete_in_tab(self):
        cron = CronTab(user=cron_user)
        for job in cron:
            if job.comment == 'Job-ID: ' + str(self.id) + " # | ## " + self.desc +" ##":
                cron.remove(job)
                cron.write()
                flash("Job deleted successfully!!" , "success")
                break


    def enable_in_tab(self):
        cron = CronTab(user=cron_user)
        job = next(cron.find_comment('Job-ID: ' +str(self.id) + " # | ## " + self.desc +" ##"))
        job.enable(True)
        cron.write()
        flash("Job enabled successfully!!" , "succsess")
    
    
    def disable_in_tab(self):
        cron = CronTab(user=cron_user)
        job = next(cron.find_comment('Job-ID: ' +str(self.id) + " # | ## " + self.desc +" ##"))
        job.enable(False)
        cron.write()
        flash("Job disabled successfully!!" , "succsess")



@app.route("/home")
@app.route("/")
def info_page():
    return render_template('infopage.html')

@app.route("/joblist")
def cronjob_list():
    cronjobs = Cronjob.query.order_by(Cronjob.id).all()
    return render_template('joblist.html' , cronjobs=cronjobs)


@app.route("/create" ,methods= ["GET" , "POST"] )
def create_job():
    if request.method == 'POST':
        cronjob = Cronjob(
                        desc = request.form['desc'],
                        minute = request.form['minute'],
                        hour = request.form['hour'],
                        day = request.form['day'],
                        month = request.form['month'],
                        dow = request.form['dow'],
                        command = request.form['command'])
        cronjob.status = True
        db.session.add(cronjob)
        db.session.commit()
        cronjob.add_to_tab()
        return redirect(url_for("cronjob_list"))

    return render_template("/create.html")


@app.route("/create/non-schedule" , methods= ["GET" , "POST"])
def create_non():
    if request.method == 'POST':
        cronjob = Cronjob(desc = request.form['desc'],command = request.form['command'])
        cronjob.status= False
        db.session.add(cronjob)
        db.session.commit()
        return redirect(url_for("cronjob_list"))
    
    return render_template("/create_non.html")


@app.route("/job/update/<int:id>" , methods =  ["GET" , "POST"])
def update_job(id):
    cronjob = db.get_or_404(Cronjob , id)
    old_desc = cronjob.desc
    if request.method == 'POST':
        cronjob.desc = request.form['desc']
        cronjob.minute = request.form['minute']
        cronjob.hour = request.form['hour']
        cronjob.day = request.form['day']
        cronjob.month = request.form['month']
        cronjob.dow = request.form['dow']
        cronjob.command = request.form['command']

        cronjob.update_in_tab(old_desc )
        db.session.commit()
        return redirect(url_for("cronjob_list"))
    
    return render_template("/update.html" , cronjob=cronjob)


@app.route("/job/delete/<int:id>" , methods =  ["GET" , "POST"] )
def delete_job(id):
    cronjob = Cronjob.query.get_or_404(id)
    db.session.delete(cronjob)
    db.session.commit()
    cronjob.delete_in_tab()

    flash("Job deleted sucsessfuly" , 'sucsess')
    return redirect(url_for("cronjob_list"))


@app.route("/job/enable/<int:id>")
def enable_job(id):
    cronjob = Cronjob.query.get_or_404(id)
    if cronjob.status == False:
        cronjob.status = True
        cronjob.enable_in_tab()
    else:
        flash('this Job is already enabled')
    db.session.commit()
    return redirect(url_for("update_job" , id=cronjob.id))


@app.route("/job/disable/<int:id>")
def disable_job(id):
    cronjob = Cronjob.query.get_or_404(id)
    if cronjob.status == False:
        flash('this Job is already disabled')
    else:
        cronjob.status = False
        cronjob.disable_in_tab()
        db.session.commit()
    return redirect(url_for("update_job" , id=cronjob.id))


@app.route("/job/execute/<int:id>")
def excute_job(id):
    cronjob = Cronjob.query.get_or_404(id)
    os.system(cronjob.command)
    return redirect(url_for("cronjob_list"))


####### Git Repos #######

from os import listdir
from os.path import isdir , join

################# put here the absolute path to your git repos ######################
################# Examble gitpath = "/home/dalil/git/" ##############################
gitpath = "/git/"

def get_repositories():
    git_dirs = [f for f in listdir(gitpath) if isdir(join(gitpath, f))]
    for i in git_dirs:
        if i[0] == '.':
            git_dirs.remove(i)
    return git_dirs

@app.route("/gitrepos")
def list_repos():
    all_reops = get_repositories()
    return render_template('git_repos.html' , repos =all_reops)


@app.route("/gitrepo/<repo_name>")
def pull_repo(repo_name):
    path = str(gitpath) + '/' + repo_name
    cmd = subprocess.Popen(['git','pull'], cwd=path , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
    cmd.communicate()
    return redirect(url_for("list_repos"))

@app.route("/gitrepo/pull_all")
def pull_repos():
    all_repos = get_repositories()
    for repo in all_repos:
        pull_repo(repo)
    return redirect(url_for("list_repos"))



if __name__== '__main__':
    with app.app_context():
        db.create_all()
    add_crontab_divider()
    app.run(port=5000,debug=True)