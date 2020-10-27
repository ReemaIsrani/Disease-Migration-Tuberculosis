# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 
import pandas as pd
import numpy as np
import requests
import base64
import pickle
import json
import tablib
# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort
from flask import jsonify
# App modules
from app        import app, lm, db, bc
from app.models import User
from app.forms  import LoginForm, RegisterForm
# dataset = tablib.Dataset()
# with open(os.path.join(os.path.dirname(__file__),'rotated_prediction.csv')) as f:
#     dataset.csv = f.read()

@app.route("/table.html")
def table():
    data = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\rotated_prediction.csv")
    # data = "/dataset.html"
     #return dataset.html
    return render_template('pages/table.html', dataa=data)
#provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Logout user
@app.route('/logout.html')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register a new user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    
    # declare the Registration Form
    form = RegisterForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template( 'pages/register.html', form=form, msg=msg )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = User.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'Error: User exists!'
        
        else:         

            pw_hash = password #bc.generate_password_hash(password)

            user = User(username, email, pw_hash)

            user.save()

            msg = 'User created, please <a href="' + url_for('login') + '">login</a>'     

    else:
        msg = 'Input error'     

    return render_template( 'pages/register.html', form=form, msg=msg )

# Authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        if user:
            
            #if bc.check_password_hash(user.password, password):
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unknown user"

    return render_template( 'pages/login.html', form=form, msg=msg ) 

# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    content = None

    try:

        # @WIP to fix this
        # Temporary solution to solve the dependencies
        if path.endswith(('.png', '.svg' '.ttf', '.xml', '.ico', '.woff', '.woff2')):
            return send_from_directory(os.path.join(app.root_path, 'static'), path)    

        # try to match the pages defined in -> pages/<input file>
        return render_template( 'pages/'+path )

    except:
        
        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/404.html' ) )

@app.route('/charts', methods=['GET'])
def map():
    district = request.args.get('name')
    df = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\tb_full.csv")
    xold=df[df["Location"]==district]
    x_axis = xold['Year']
    y_axis= xold['total_cases'] 
    name=df['Location'].unique()
    rate=y_axis.pct_change()
    rate=round(rate.fillna(value=0),4)
    rate=rate.replace(np.inf, 0)
    line_labelsold=round(x_axis,2)
    line_valuesold=round(y_axis,2)
    smear=xold["smear"]
    data_points_0 = zip(line_labelsold,line_valuesold,smear,rate)
    df1=pd.concat([x_axis,rate],axis=1)
    df1.columns=['Year','Total Cases Spread rate']
    df1.reset_index(drop=True, inplace=True)
    path=r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\templates\pages\\"+district+".csv"
    df1.to_csv(path)
    return render_template('pages/charts.html', title=district,my_list=data_points_0)

@app.route('/graphs', methods=['GET','POST'])
def value():
    
    district = request.args.get('name')
    if request.method == 'POST':
        so = request.form.get('so')
        no = request.form.get('no')
        rspmm = request.form.get('rspm')
        rainfall = request.form.get('rainfall')
        temperature = request.form.get('temperature')
        humidity = request.form.get('humidity')
    
    loc=district
    no2=no
    so2=so
    rspm=rspmm
    print(loc,no2,so2,rspm,rainfall,temperature,humidity)
    data={'loc':loc,'rspm':int(rspm),'no2':int(no2),'so2':int(so2),'rainfall':int(rainfall),'temperature':int(temperature),'humidity':int(humidity)}
    response = requests.post('https://beprojectdm.pythonanywhere.com/dm',data=json.dumps(data)).json()
    
    df1=pickle.loads(base64.b64decode(response['prediction'].encode()))
    df2=pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\tb_yearly.csv")
    dff=df2.append(df1)
    dff.to_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\prediction2.csv")
    x=dff[dff["Location"]==loc]
    x_axis = x['Year']
    y_axis= x['total_cases']
    smearnew=x["smear"]
    ratenew=y_axis.pct_change()
    ratenew=round(ratenew.fillna(value=0),4)
    ratenew=ratenew.replace(np.inf, 0)
    name=dff['Location'].unique()
    line_labelsnew=round(x_axis,2)
    line_valuesnew=round(y_axis,2)
    data_points_1 = zip(line_labelsnew,line_valuesnew,smearnew,ratenew)

    df3=pd.concat([x_axis,ratenew],axis=1)
    df3.columns=['Year','Total Cases Spread rate']
    df3.reset_index(drop=True, inplace=True)
    path=r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\templates\pages\\"+district+"_retrain.csv"
    df3.to_csv(path)

    # df1 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\predicted.csv")
    df = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\tb_full.csv")
    xold=df[df["Location"]==district]
    x_axis = xold['Year']
    y_axis= xold['total_cases'] 
    rateold=y_axis.pct_change()
    rateold=round(rateold.fillna(value=0),4)
    rateold=rateold.replace(np.inf, 0)
    name=df['Location'].unique()
    line_labelsold=round(x_axis,2)
    line_valuesold=round(y_axis,2)
    smearold=xold["smear"]
    data_points_0 = zip(line_labelsold,line_valuesold,smearold,rateold)
    
    return render_template('pages/graphs.html', title=district,my_list=data_points_0,my_list_1=data_points_1,rainfall=rainfall,temperature=temperature,humidity=humidity)

@app.route('/triple', methods=['POST'])
def triple():
    district = request.args.get('name')
    if request.method == 'POST':
        so = request.values.get('so')
        no = request.values.get('no')
        rspmm = request.values.get('rspm')
        rainfall = request.values.get('rainfall')
        temperature = request.values.get('temperature')
        humidity = request.values.get('humidity')
    
    loc=district
    no2=no
    so2=so
    rspm=rspmm
    data={'loc':loc,'rspm':int(rspm),'no2':int(no2),'so2':int(so2),'rainfall':int(rainfall),'temperature':int(temperature),'humidity':int(humidity)}
    response = requests.post('https://beprojectdm.pythonanywhere.com/dm',data=json.dumps(data)).json()
    
    df1=pickle.loads(base64.b64decode(response['prediction'].encode()))
    df2=pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\tb_yearly.csv")
    dff=df2.append(df1)
    x=dff[dff["Location"]==loc]
    x_axis = x['Year']
    y_axis= x['total_cases']
    smearnew=x["smear"]
    ratenew=y_axis.pct_change()
    ratenew=round(ratenew.fillna(value=0),4)
    ratenew=ratenew.replace(np.inf, 0)
    name=dff['Location'].unique()
    line_labelsnew=round(x_axis,2)
    line_valuesnew=round(y_axis,2)
    data_points_2 = zip(line_labelsnew,line_valuesnew,smearnew,ratenew)

    df3=pd.concat([x_axis,ratenew],axis=1)
    df3.columns=['Year','Total Cases Spread rate']
    df3.reset_index(drop=True, inplace=True)
    path=r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\templates\pages\\"+district+"_retrain.csv"
    df3.to_csv(path)

    # df1 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\predicted.csv")
    df = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\tb_full.csv")
    xold=df[df["Location"]==district]
    x_axis = xold['Year']
    y_axis= xold['total_cases'] 
    rateold=y_axis.pct_change()
    rateold=round(rateold.fillna(value=0),4)
    rateold=rateold.replace(np.inf, 0)
    name=df['Location'].unique()
    line_labelsold=round(x_axis,2)
    line_valuesold=round(y_axis,2)
    smearold=xold["smear"]
    data_points_0 = zip(line_labelsold,line_valuesold,smearold,rateold)

    dff=pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\prediction2.csv")
    x=dff[dff["Location"]==loc]
    x_axis = x['Year']
    y_axis= x['total_cases']
    smearneww=x["smear"]
    rateneww=y_axis.pct_change()
    rateneww=round(rateneww.fillna(value=0),4)
    rateneww=rateneww.replace(np.inf, 0)
    name=dff['Location'].unique()
    line_labelsneww=round(x_axis,2)
    line_valuesneww=round(y_axis,2)
    data_points_1 = zip(line_labelsneww,line_valuesneww,smearneww,rateneww)
    
    return render_template('pages/triple.html', title=district,my_list=data_points_0,my_list_1=data_points_1,my_list_2=data_points_2)

@app.route('/bar', methods=['GET'])
def bar():
    
    df = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\india_all_sum.csv")
    x_axis = df['Year']
    y_axis= df['total_cases'] 
    z_axis= df['smear']
    
    data_points = zip(x_axis,y_axis)
    data_points_smear = zip(x_axis,z_axis)
    #,smear,ratey,ratez
    
    return render_template('pages/bar.html', list=list(data_points),lists=list(data_points_smear))
    

@app.route('/india_line', methods=['GET'])
def line():
    
    df = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\india_all_sum.csv")
    x_axis = df['Year']
    y_axis= df['total_cases'] 
    rate=y_axis.pct_change()
    rate=round(rate.fillna(value=0),4)
    line_labelsold=round(x_axis,2)
    line_valuesold=round(y_axis,2)
    smear=round(df["smear"],2)
    data_points_0 = zip(line_labelsold,line_valuesold,smear,rate)

    return render_template('pages/india_linechart.html',my_list=data_points_0)

@app.route('/stats.html', methods=['GET'])
def stats():
    
    df1 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_totalcases.csv")
    df2 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_smearpositivecases.csv")
    df3 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_totalcases.csv")
    df4 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_smearpositivecases.csv")
    gbr_1=df3['gbr']
    gbr_2=df1['gbr']
    gbr_3=df4['gbr']
    gbr_4=df2['gbr']
    #,smear,ratey,ratez
    
    return render_template('pages/stats.html',train_total=gbr_1,test_total=gbr_2,train_smear=gbr_3,test_smear=gbr_4 )

@app.route('/model2.html', methods=['GET'])
def model2():
    
    df1 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_totalcases.csv")
    df2 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_smearpositivecases.csv")
    df3 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_totalcases.csv")
    df4 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_smearpositivecases.csv")
    rfr_1=df3['rfr']
    rfr_2=df1['rfr']
    rfr_3=df4['rfr']
    rfr_4=df2['rfr']
    #,smear,ratey,ratez
    
    return render_template('pages/model2.html',train_total=rfr_1,test_total=rfr_2,train_smear=rfr_3,test_smear=rfr_4 )

@app.route('/model3.html', methods=['GET'])
def model3():
    
    df1 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_totalcases.csv")
    df2 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_smearpositivecases.csv")
    df3 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_totalcases.csv")
    df4 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_smearpositivecases.csv")
    dtr_1=df3['dtr']
    dtr_2=df1['dtr']
    dtr_3=df4['dtr']
    dtr_4=df2['dtr']
    #,smear,ratey,ratez
    
    return render_template('pages/model3.html',train_total=dtr_1,test_total=dtr_2,train_smear=dtr_3,test_smear=dtr_4 )

@app.route('/model4.html', methods=['GET'])
def model4():
    
    df1 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_totalcases.csv")
    df2 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_smearpositivecases.csv")
    df3 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_totalcases.csv")
    df4 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_smearpositivecases.csv")
    xgbr_1=df3['xgbr']
    xgbr_2=df1['xgbr']
    xgbr_3=df4['xgbr']
    xgbr_4=df2['xgbr']
    #,smear,ratey,ratez
    
    return render_template('pages/model4.html',train_total=xgbr_1,test_total=xgbr_2,train_smear=xgbr_3,test_smear=xgbr_4 )

@app.route('/model5.html', methods=['GET'])
def model5():
    
    df1 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_totalcases.csv")
    df2 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_test_smearpositivecases.csv")
    df3 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_totalcases.csv")
    df4 = pd.read_csv(r"C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\plot_train_smearpositivecases.csv")
    nn_1=df3['nn']
    nn_2=df1['nn']
    nn_3=df4['nn']
    nn_4=df2['nn']
    #,smear,ratey,ratez
    
    return render_template('pages/model5.html',train_total=nn_1,test_total=nn_2,train_smear=nn_3,test_smear=nn_4 )

@app.route('/correlation.html', methods=['POST'])
def corr1():
    if request.method =='POST':
        if request.args.get('list')!=None:  
            value=request.args.get('value_change')
            col_head=request.args.get('id')
            selected_list=request.args.get('list')
            print('value',value,'col_head',col_head,'selected_list',selected_list)
            df=pd.read_csv(r'C:/Users/Ritika/AppData/Local/Programs/Python/Python37/DMWebapp/app/combinations.csv')
            df=df.iloc[:,[0,1,2,3,4,5,6,7]]

            if(col_head=='year' or col_head=='quarter'):
                value=int(value)
            df1=df[df[col_head]==value]
            rspmmm=df1['rspm'].unique().tolist()
            nooo2=df1['no2'].unique().tolist()
            sooo2=df1['so2'].unique().tolist()
            rainfallll=df1['rainfall'].unique().tolist()
            humidityyy=df1['humidity'].unique().tolist()
            temperaturee=df1['temperature'].unique().tolist()
            yearrr=df1['year'].unique().tolist()
            quarterrr=df1['quarter'].unique().tolist()
            yearrr.sort()
            quarterrr.sort()  
            print(rspmmm) 
            # return render_template('pages/correlation.html',rspmmm=rspmmm,nooo2=nooo2,sooo2=sooo2,rainfallll=rainfallll,humidityyy=humidityyy,temperaturee=temperaturee,yearrr=yearrr,quarterrr=quarterrr,selected_list=selected_list)
            final_list={'rspm':rspmmm,'no2':nooo2,'so2':sooo2,'rainfall':rainfallll,'humidity':humidityyy,'temperature':temperaturee,'year':yearrr,'quarter':quarterrr,'selected_list':selected_list}
            return jsonify(final_list)
        elif request.values.get('rspm')!=None:
            print("hello")
            rspm = request.values.get('rspm')
            no2 = request.values.get('no2')
            so2 = request.values.get('so2')
            year = request.values.get('year')
            rainfall = request.values.get('rainfall')
            temperature = request.values.get('temperature')
            humidity = request.values.get('humidity')
            quarter = request.values.get('quarter')
            year=int(year)
            quarter=int(quarter)
            print(rspm,so2,no2,year,rainfall,temperature,humidity,quarter)
            df=pd.read_csv(r'C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\correlation.csv')
            df.columns=['Location','Year','Quarter','totalcases','smearpositivecases','rainfall','humidity','temperature','so2','no2','rspm']
            table=[]
            table.append(['rainfall_low','x','750'])
            table.append(['rainfall_moderate','751','2350'])
            table.append(['rainfall_high','2351','x'])
            table.append(['temperature_low','x','20'])
            table.append(['temperature_moderate','21','30'])
            table.append(['temperature_high','31','x'])
            table.append(['humidity_low','x','50'])
            table.append(['humidity_high','51','x'])
            table.append(['rspm_good','x','50'])  
            table.append(['rspm_satisfactory','51','100'])
            table.append(['rspm_moderate','101','200'])
            table.append(['rspm_poor','201','300'])
            table.append(['rspm_severe','301','x'])
            table.append(['no2_safe','x','25'])
            table.append(['no2_potential','26','50'])
            table.append(['no2_curtailing','51','100'])
            table.append(['no2_hazardous','101','x'])
            table.append(['so2_safe','x','25'])
            table.append(['so2_potential','26','50'])
            table.append(['so2_curtailing','51','100'])


            ranges=pd.DataFrame(table,columns=['category','low','high'])

            try:
            
                df1=df[df['Year']==year]
                df2=df1[df1['Quarter']==quarter]

                    


                rspm1=ranges[ranges['category']==rspm].iloc[0,:]
                if(str(rspm1['low'])=='x'):
                    df3=df2[df2['rspm']<=int(rspm1['high'])]
                elif(str(rspm1['high'])=='x'):
                    df3=df2[df2['rspm']>=int(rspm1['low'])]
                else:
                    df3=df2[df2['rspm'].between(int(rspm1['low']),int(rspm1['high']),inclusive=True)]



                    # In[71]:


                so21=ranges[ranges['category']==so2].iloc[0,:]
                if(str(so21['low'])=='x'):
                    df4=df3[df3['so2']<=int(so21['high'])]
                elif(str(so21['high'])=='x'):
                    df4=df3[df3['so2']>=int(so21['low'])]
                else:
                    df4=df3[df3['so2'].between(int(so21['low']),int(so21['high']),inclusive=True)]



                    # In[72]:


                no21=ranges[ranges['category']==no2].iloc[0,:]
                if(str(no21['low'])=='x'):
                    df5=df4[df4['no2']<=int(no21['high'])]
                elif(str(no21['high'])=='x'):
                    df5=df4[df4['no2']>=int(no21['low'])]
                else:
                    df5=df4[df4['no2'].between(int(no21['low']),int(no21['high']),inclusive=True)]



                    # In[73]:


                humidity1=ranges[ranges['category']==humidity].iloc[0,:]
                if(str(humidity1['low'])=='x'):
                    df6=df5[df5['humidity']<=int(humidity1['high'])]
                elif(str(humidity1['high'])=='x'):
                    df6=df5[df5['humidity']>=int(humidity1['low'])]
                else:
                    df6=df5[df5['humidity'].between(int(humidity1['low']),int(humidity1['high']),inclusive=True)]


                    # In[74]:


                rainfall1=ranges[ranges['category']==rainfall].iloc[0,:]
                if(str(rainfall1['low'])=='x'):
                    df7=df6[df6['rainfall']<=int(rainfall1['high'])]
                elif(str(rainfall1['high'])=='x'):
                    df7=df6[df6['rainfall']>=int(rainfall1['low'])]
                else:
                    df7=df6[df6['rainfall'].between(int(rainfall1['low']),int(rainfall1['high']),inclusive=True)]

                    

                    # In[75]:


                temperature1=ranges[ranges['category']==temperature].iloc[0,:]
                if(str(temperature1['low'])=='x'):
                    df8=df7[df7['temperature']<=int(temperature1['high'])]
                elif(str(temperature1['high'])=='x'):
                    df8=df7[df7['temperature']>=int(temperature1['low'])]
                else:
                    df8=df7[df7['temperature'].between(int(temperature1['low']),int(temperature1['high']),inclusive=True)]


                df9=df8.iloc[:,[0,3,4]]
                l=[x for x in df9["Location"]]
                print(l)
                if not l:
                    l=['-1']
                return render_template('pages/correlation.html',list1=l,year=year,quarter=quarter,rainfall=rainfall,temperature=temperature,humidity=humidity,rspm=rspm,so2=so2,no2=no2)

            except:
                return ['-1']
        
            
            # return Error
        
            

            
    return render_template('pages/correlation.html')

# @app.route('/correlation', methods=['POST'])
# def corr2():

#     if request.method == 'POST' and 
        
#     return render_template('pages/correlation.html')
@app.route('/pie', methods=['GET'])
def pie():
    year=request.args.get('year')
    quarter=request.args.get('quarter')
    rspm=request.args.get('rspm') 
    so2=request.args.get('so2')
    no2=request.args.get('no2')
    rainfall=request.args.get('rainfall')
    temperature=request.args.get('temperature')
    humidity=request.args.get('humidity')
    
    year=int(year)
    quarter=int(quarter)
    print(rspm,so2,no2,year,rainfall,temperature,humidity,quarter)
    df=pd.read_csv(r'C:\Users\Ritika\AppData\Local\Programs\Python\Python37\DMWebapp\app\correlation.csv')
    df.columns=['Location','Year','Quarter','totalcases','smearpositivecases','rainfall','humidity','temperature','so2','no2','rspm']
    table=[]
    table.append(['rainfall_low','x','750'])
    table.append(['rainfall_moderate','751','2350'])
    table.append(['rainfall_high','2351','x'])
    table.append(['temperature_low','x','20'])
    table.append(['temperature_moderate','21','30'])
    table.append(['temperature_high','31','x'])
    table.append(['humidity_low','x','50'])
    table.append(['humidity_high','51','x'])
    table.append(['rspm_good','x','50']) 
    table.append(['rspm_satisfactory','51','100'])
    table.append(['rspm_moderate','101','200'])
    table.append(['rspm_poor','201','300'])
    table.append(['rspm_severe','301','x'])
    table.append(['no2_safe','x','25'])
    table.append(['no2_potential','26','50'])
    table.append(['no2_curtailing','51','100'])
    table.append(['no2_hazardous','101','x'])
    table.append(['so2_safe','x','25'])
    table.append(['so2_potential','26','50'])
    table.append(['so2_curtailing','51','100'])


    ranges=pd.DataFrame(table,columns=['category','low','high'])


    
    df1=df[df['Year']==year]
    df2=df1[df1['Quarter']==quarter]

        


    rspm1=ranges[ranges['category']==rspm].iloc[0,:]
    if(str(rspm1['low'])=='x'):
        df3=df2[df2['rspm']<=int(rspm1['high'])]
    elif(str(rspm1['high'])=='x'):
        df3=df2[df2['rspm']>=int(rspm1['low'])]
    else:
        df3=df2[df2['rspm'].between(int(rspm1['low']),int(rspm1['high']),inclusive=True)]



        # In[71]:


    so21=ranges[ranges['category']==so2].iloc[0,:]
    if(str(so21['low'])=='x'):
        df4=df3[df3['so2']<=int(so21['high'])]
    elif(str(so21['high'])=='x'):
        df4=df3[df3['so2']>=int(so21['low'])]
    else:
        df4=df3[df3['so2'].between(int(so21['low']),int(so21['high']),inclusive=True)]



        # In[72]:


    no21=ranges[ranges['category']==no2].iloc[0,:]
    if(str(no21['low'])=='x'):
        df5=df4[df4['no2']<=int(no21['high'])]
    elif(str(no21['high'])=='x'):
        df5=df4[df4['no2']>=int(no21['low'])]
    else:
        df5=df4[df4['no2'].between(int(no21['low']),int(no21['high']),inclusive=True)]



        # In[73]:


    humidity1=ranges[ranges['category']==humidity].iloc[0,:]
    if(str(humidity1['low'])=='x'):
        df6=df5[df5['humidity']<=int(humidity1['high'])]
    elif(str(humidity1['high'])=='x'):
        df6=df5[df5['humidity']>=int(humidity1['low'])]
    else:
        df6=df5[df5['humidity'].between(int(humidity1['low']),int(humidity1['high']),inclusive=True)]


        # In[74]:


    rainfall1=ranges[ranges['category']==rainfall].iloc[0,:]
    if(str(rainfall1['low'])=='x'):
        df7=df6[df6['rainfall']<=int(rainfall1['high'])]
    elif(str(rainfall1['high'])=='x'):
        df7=df6[df6['rainfall']>=int(rainfall1['low'])]
    else:
        df7=df6[df6['rainfall'].between(int(rainfall1['low']),int(rainfall1['high']),inclusive=True)]

        

        # In[75]: 


    temperature1=ranges[ranges['category']==temperature].iloc[0,:]
    if(str(temperature1['low'])=='x'):
        df8=df7[df7['temperature']<=int(temperature1['high'])]
    elif(str(temperature1['high'])=='x'):
        df8=df7[df7['temperature']>=int(temperature1['low'])]
    else:
        df8=df7[df7['temperature'].between(int(temperature1['low']),int(temperature1['high']),inclusive=True)]

    dfff=df8.iloc[:,[0,3,4]]
    dft=[x for x in dfff["totalcases"]]
    dfl=[x for x in dfff["Location"]]
    dfs=[x for x in dfff["smearpositivecases"]]
    df9=list(zip(dft,dfl,dfs))
    print(df9)
    return render_template('pages/pie.html',df=df9,rspm=rspm,so2=so2,no2=no2,rainfall=rainfall,temperature=temperature,humidity=humidity)

@app.route('/pass_val', methods=['POST'])
def pass_val():
    
    value=request.args.get('value_change')
    col_head=request.args.get('id')
    selected_list=request.args.get('list')
    print('value',value,'col_head',col_head,'selected_list',selected_list)
    df=pd.read_csv(r'C:/Users/Ritika/AppData/Local/Programs/Python/Python37/DMWebapp/app/combinations.csv')
    df=df.iloc[:,[0,1,2,3,4,5,6,7]]

    if(col_head=='year' or col_head=='quarter'):
        value=int(value)
    df1=df[df[col_head]==value]
    rspmmm=df1['rspm'].unique().tolist()
    nooo2=df1['no2'].unique().tolist()
    sooo2=df1['so2'].unique().tolist()
    rainfallll=df1['rainfall'].unique().tolist()
    humidityyy=df1['humidity'].unique().tolist()
    temperaturee=df1['temperature'].unique().tolist()
    yearrr=df1['year'].unique().tolist()
    quarterrr=df1['quarter'].unique().tolist()
    yearrr.sort()
    quarterrr.sort()   
    return jsonify({'reply':'success'})
     
