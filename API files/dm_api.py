from flask import Flask, request, jsonify
import traceback
import base64
import pickle
import pandas as pd
from keras.models import load_model
app = Flask(__name__)

@app.route('/dm', methods=['POST','GET'])
def clustering():
    try:
        if request.method == 'POST':
            data=request.get_json(force=True)
            loc=data['loc']
            so2=data['so2']/100
            no2=data['no2']/100
            rspm=data['rspm']/100
            rainfall=data['rainfall']/100
            temperature=data['temperature']/100
            humidity=data['humidity']/100
            df=pd.read_csv('forecasted.csv')

            df=df[df['Location']==loc].reset_index(drop=True)

            print(df.head())
            index=0
            for row in df.itertuples():
                temp_so2=row[4]
                temp_no2=row[5]
                temp_rspm=row[6]
                temp_rain=row[7]
                temp_temp=row[8]
                temp_humid=row[9]
                df.iloc[index,3]=temp_so2*(1+so2)
                df.iloc[index,4]=temp_no2*(1+no2)
                df.iloc[index,5]=temp_rspm*(1+rspm)
                df.iloc[index,6]=temp_rain*(1+rainfall)
                df.iloc[index,7]=temp_temp*(1+temperature)
                df.iloc[index,8]=temp_humid*(1+humidity)
                index=index+1

            print(df.head())
            loc_index=pd.read_csv('loc_index.csv')
            loc_index=[loc_index[loc_index['location']==loc]]
            list_loc=[0 for i in range(214)]
            list_loc[int(loc_index[0]['column'])]=1
            lists_loc=[list_loc for i in range(28)]
            loc_encoded=pd.DataFrame(lists_loc)

            quarter_encoded=pd.get_dummies(df['Quarter'])

            quarter_encoded.columns=['q1','q2','q3','q4']
            variables = ['RAINFALL','HUMIDITY','TEMPERATURE','SO2','NO2','RSPM']
            features = pd.DataFrame(df.loc[:, variables].values,columns=variables)

            x_t=pd.concat([loc_encoded,quarter_encoded,features],axis=1)
            x_s=pd.concat([loc_encoded,quarter_encoded,features],axis=1)


            means_t=[341.37461283,  61.73049471,  25.36413742,  10.17907045,23.38506682, 109.64026525]
            vari_t=[1.84967567e+05, 3.90749355e+02, 1.92951825e+01, 6.42141023e+01,2.78785660e+02, 4.69270620e+04]
            x_t[variables]=scale_data(x_t[variables],means_t,vari_t)

            NN = load_model('total_cases.h5')
            totalcases=NN.predict(x_t)

            means_s=[336.54684355,  61.59908028,  25.393144  ,  10.18898447,23.28807315, 107.6921276 ]
            vari_s=[1.78162239e+05, 3.90240538e+02, 1.93782251e+01, 6.46660757e+01,2.76890901e+02, 3.02099542e+04]
            x_s[variables]=scale_data(x_s[variables],means_s,vari_s)

            NN = load_model('total_smearpositivecases.h5')
            smcases=NN.predict(x_s)

            output=pd.DataFrame(totalcases,columns=['total_cases'])
            output['smear']=smcases


            output['Year']=df['Year']
            output['Quarter']=df['Quarter']
            output['Location']=[loc for i in range(28)]

            output=pd.DataFrame(output.groupby(['Location','Year'])['total_cases','smear'].sum()).reset_index()

            output['Year']=output['Year'].astype('int64')
            output['total_cases']=output['total_cases'].astype('int64')
            output['smear']=output['smear'].astype('int64')

            pickled = pickle.dumps(output)
            pickled_b64 = base64.b64encode(pickled)
            hug_pickled_str = pickled_b64.decode('utf-8')
            return jsonify({'prediction': hug_pickled_str})
    except:
        return jsonify({'trace': traceback.format_exc()})

def scale_data(df,means,stds):

    index=0
    for col in df.columns:
        df[col]=(df[col]-means[index])/(stds[index] ** 0.5)
        index=index+1

    return df
if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except:
        port = 5000
    app.run(port=port, debug=True)
