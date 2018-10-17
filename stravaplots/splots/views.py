# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render,redirect
from django.http import HttpResponse


from forms import TokenForm

from matplotlib.figure import Figure                      
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pylab as plt

import numpy as np
import cStringIO

import GPy

import stravalib
from stravalib.client import Client


# Create your views here.
def index(request):
    return render(request,'splots/index.html',{})

def clear_session(request):
    if 'access_token' in request.session:
        del request.session['access_token']
    return redirect('/splots/')

def make_plot(request):
    if 'access_token' in request.session:
        context_dict = {}
        if request.method == 'POST':
            token_form = TokenForm(request.POST)
            if token_form.is_valid():
                # do the stuff
                # context_dict['token'] = token_form.cleaned_data['token_field']
                context_dict['n_recent'] = token_form.cleaned_data['n_recent']
                dt = token_form.cleaned_data['from_date']
                dts = "{}-{}-{}".format(dt.year,dt.month,dt.day)
                context_dict['year'] = dt.year
                context_dict['month'] = dt.month
                context_dict['day'] = dt.day
            else:
                context_dict['token_form'] = token_form
        else:
            token_form = TokenForm()
            context_dict['token_form'] = token_form
        print context_dict
        return render(request,'splots/make_plot.html',context_dict)
    else:
        return authenticate(request)

def get_data(token,year,month,day):
    max_elevation_gain = 100
    max_distance = 10000
    min_hr = 110
    print token
    client = Client()
    client.access_token = token
    client.get_athlete()
    print client
    # weird stuff to stop the assertion error
    import arrow
    from datetime import datetime
    from_date = "{}-{:02d}-{:02d}".format(year,int(month),int(day))
    dt = arrow.get(from_date).datetime
    activities = client.get_activities(after = dt)
    just_runs = filter(lambda a: a.type=="Run",activities)
    flat_runs = filter(lambda a: a.total_elevation_gain.num<=max_elevation_gain and a.distance.num <= max_distance,just_runs)
    summaries = []
    for a in flat_runs:
        summaries.append((a.start_date,a.distance,a.average_heartrate,a.average_speed))
    summaries = filter(lambda x: x[2]>=min_hr,summaries)
    summaries = sorted(summaries,key = lambda x: x[0])
    

    athlete = client.get_athlete()
    name = "{} {}".format(athlete.firstname,athlete.lastname)

    return summaries,name

    


def make_image(request,n_recent,year,month,day):
    n_recent = int(n_recent)
    x = np.arange(0,10,0.1)
    y = np.sin(x)
    token = request.session.get('access_token',None)
    if token:
        summaries,name = get_data(token,year,month,day)

        hr = [d[2] for d in summaries]
        avs = [(1.0/d[3].num)*1000.0/60.0 for d in summaries]

        end = len(summaries) - n_recent
        m = GPy.models.GPRegression(np.array(hr)[:end,None],np.array(avs)[:end,None])
        m.optimize('bfgs')
        # f = m.plot(plot_limits = (min(hr),max(hr)),figsize=(20,10),fontsize=16)
        # plt.xlabel('mean heart rate',fontsize=24)
        # plt.ylabel('mean pace (min per km)',fontsize=24)
        n_data = len(hr)
        # n_recent = 20


        fig = Figure(figsize=[10,5])   
        # plt.plot(x,y)                            
        ax = fig.add_axes([.1,.1,.8,.8])                          
        ax.plot(hr,avs,'k+')  
        ax.set_title(name)
        pred_x = np.arange(min(hr),max(hr),0.1)
        f,va = m.predict(pred_x[:,None])
        ql,qu = m.predict_quantiles(pred_x[:,None])
        ax.plot(pred_x,ql,'b--')
        ax.plot(pred_x,qu,'b--')
        ax.plot(pred_x,f,'b')
        canvas = FigureCanvasAgg(fig)
        ax.set_xlabel('Mean heart rate (bpm)',fontsize=16)
        ax.set_ylabel('Mean pace (min per km)',fontsize=16)

        m2 = GPy.models.GPRegression(np.array(hr[-n_recent:])[:,None],np.array(avs[-n_recent:])[:,None])
        m2.optimize('bfgs')
        pred_x = np.arange(min(hr[-n_recent:]),max(hr[-n_recent:]),0.1)
        f,va = m2.predict(pred_x[:,None])
        ql,qu = m2.predict_quantiles(pred_x[:,None])
        ax.plot(pred_x,f,'r')
        ax.plot(pred_x,ql,'r--')
        ax.plot(pred_x,qu,'r--')
        ax.grid()

        ytv = ["4:00","4:30","5:00","5:30","6:00","6:30","7:00"]
        ax.set_yticks(np.arange(4,7,0.5))
        ax.set_yticklabels(ytv)

        m_size = 1
        max_marker_size = 20
        m_step = (max_marker_size - m_size)/(1.0*n_recent)

        for i in range(n_data-n_recent,n_data):
            ax.plot(hr[i],avs[i],'ro',markersize=m_size)
        #     plt.plot([hr[i-1],hr[i]],[avs[i-1],avs[i]],'k--')
            month = summaries[i][0].date().month
            day = summaries[i][0].date().day
            short_date = "{}/{}".format(day,month)
            ax.text(hr[i],avs[i],short_date,fontsize=8)
            m_size += m_step

        # write image data to a string buffer and get the PNG image bytes
        buf = cStringIO.StringIO()
        canvas.print_png(buf)
        data = buf.getvalue()

        # Send buffer in a http response the the browser with the mime type image/png set
        return HttpResponse(data, content_type="image/png")
    else:
        return HttpResponse("No")

def authenticate(request):
    redirurl = 'https://www.strava.com/oauth/authorize/'
    redirurl += '?client_id=22245'
    redirurl += '&response_type=code'
    redirurl += '&approval_prompt=force'
    redirurl += '&scope=public'
    redirurl += '&redirect_uri=http://localhost:8000/splots/exchange'
    redirurl += '&state=a'
    print redirurl
    return redirect(redirurl)

def exchange(request):
    import requests
    code = request.GET['code']
    redirurl = 'https://www.strava.com/oauth/token'
    params = {}
    params['code'] = code
    params['client_id'] = '22245'
    params['client_secret'] = 'ae4e743a5e87baca1530ac16f59f941096b36536'
    response = requests.post(redirurl,params = params)
    access_token = response.json()['access_token']
    request.session['access_token'] = access_token
    return redirect('/splots/')