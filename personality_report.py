import pandas as pd, numpy as np, matplotlib.pyplot as plt
import random,itertools,re, glob, os
from scipy.stats import norm
from datetime import datetime
import sys



###
# gathering data
###
time = datetime.strftime(datetime.now(),'%m/%d/%y %H:%M')+' PM Eastern'
categories = ['Openness','Conscientiousness','Extraversion','Agreeableness','Neuroticism']
completed = list(pd.read_csv('completed.csv')['Completed'])
csv_filename = glob.glob('Study*.csv')[0]
responses = pd.read_csv(csv_filename).filter(regex='(Q337|Q93|Q351|Q352|ResponseId|Q338#1_1|Q338#2_1|Q338#3_1)+')[2:]
responses = responses[~responses.isin(completed)]
os.remove(csv_filename)

#matching data
twin_data = pd.read_csv('twin_data.csv')
clinic_data = pd.read_csv('clinic_data.csv')
all_records = pd.concat([twin_data, clinic_data]).reset_index()

month_to_number = {
    'January':"1",
    'February':"2",
    'March':"3",
    'April':"4",
    'May':"5",
    'June':"6",
    'July':"7",
    'August':"8",
    'September':"9",
    'October':"10",
    'November':"11",
    'December':"12"
}


###
# scoring responses
###
distributions = {'Openness':(3.72,.51),
                 'Conscientiousness':(3.76,.51),
                 'Extraversion':(3.48,.6),
                 'Agreeableness':(4.11,.45),
                 'Neuroticism':(2.46,.63)}

scoring_dict_raw = {
    'Neuroticism': ' 1R, 11, 21R, 31, 41R, 51, 61, 71R, 81, 91, 6, 16R, 26, 36R, 46, 56R, 66, 76R, 86, 96',
    'Agreeableness': ' 2R, 12, 22, 32R, 42, 52R, 62R, 72, 82R, 92, 7, 17R, 27, 37R, 47, 57, 67R, 77R, 87R, 97R',
    'Conscientiousness': ' 3, 13R, 23R, 33R, 43, 53R, 63, 73, 83R, 93R, 8R, 18, 28, 38, 48R, 58, 68R, 78R, 88, 98',
    'Extraversion': ' 4, 14R, 24R, 34R, 44, 54R, 64R, 74, 84, 94, 9, 19, 29R, 39, 49R, 59, 69, 79R, 89, 99R',
    'Openness': ' 5, 15R, 25, 35, 45R, 55R, 65, 75, 85R, 95, 10, 20, 30, 40, 50R, 60R, 70, 80R, 90R, 100'}

###
# Adjusting reversed questions
###
scoring_dict = {}
reverse = {}
for factor in categories:
    for x in re.findall(re.compile('(?<= )\d{1,3}R?'), scoring_dict_raw[factor]):

        if 'R' in x:
            scoring_dict['Q93_{}'.format(x[:-1])] = factor
            reverse['Q93_{}'.format(x[:-1])] = 'R'
        else:
            scoring_dict['Q93_{}'.format(x)] = factor
            reverse['Q93_{}'.format(x)] = 'S'

scores = {}
Questions = list(responses)[1:]

#iterating over all responses and formatting their scores for each personality question
emails = {}
names = {}
WaldmanIDs = {}


f = open("matching_log_{}.txt".format(re.sub('/','_',str(time[:8]))), "w")


for index, row in responses.iterrows():
    #verifying identity
    try:
        DOB = "{}/{}/{}".format(month_to_number[row['Q338#1_1']],row['Q338#2_1'],row['Q338#3_1'])
        info = all_records[(all_records['User_ID'] == row['Q337'].upper()) & (all_records['DOB'] == DOB)]
        
        if len(info) > 0:
            f.write("Matched {} and {}\n".format(row['Q337'],DOB))
        else:
            f.write("Failed to match {} and {}: possible corrections\n".format(row['Q337'],DOB))
            correction_df = all_records[(all_records['User_ID'] == row['Q337'].upper()) | (all_records['DOB'] == DOB)]
            if len(correction_df) > 0:
                f.write(str(correction_df))
            else:
                f.write('No corrections found\n')
        
    except:
        pass




    scores_list = {x: [3] for x in categories}

    for Q in Questions:
        try:
            if reverse[Q] == 'R':
                scores_list[scoring_dict[Q]].append(6 - int(row[Q][0]))
            else:
                scores_list[scoring_dict[Q]].append(int(row[Q][0]))
        except:
            pass
    
    
    # creating score dictionary indexed by Qualtrics ResponseId
    try:
        scores[row['ResponseId']] = ({x: np.mean(scores_list[x]) for x in scores_list}) #ResponseId
    except:
        scores[row['ResponseId']] = ({x:0 for x in scores_list})
        
    f.write('\n')
    f.write(str(scores_list))
    f.write('\n')
    f.write('*************')
    f.write('\n')
    ##
    # Storing peripheral keys associated with Qualtrics ResponseId (email, name, Waldman ID)
    ##
   

    if isinstance(row['Q351'],str): #if email field is not empty
        emails[row['ResponseId']] = row['Q351'] 
    else:
        emails[row['ResponseId']] = ''
        

    if isinstance(row['Q352'],str): #if name field is not empty
        name = row['Q352']
        
        # converting from Last, First Middle to First Last
        name = re.sub(',','',name)
        name_list = re.findall(re.compile('\w+'), name)
        if len(name_list) > 1:
            name = '{} {}'.format(name_list[1], name_list[0])
       
        names[row['ResponseId']] = name
    else:
        names[row['ResponseId']] = ''
        
        

    if isinstance(row['Q337'],str): #if WaldmanID field is not empty
        WaldmanIDs[row['ResponseId']] = row['Q337'] 
    else:
        WaldmanIDs[row['ResponseId']] = ''
        
f.close()
    
    ##
    # End
    ##

# converting dictionary to pandas DataFrame
score_df = pd.DataFrame(scores).transpose().dropna()


##
# adding completed reports to csv
##
completed += list(score_df.index)
completed_df = pd.DataFrame()
completed_df['Completed'] = completed
#completed_df.to_csv('completed.csv')
#score_df = score_df.loc[~(score_df == 0).all(axis=1)]
##
# End
##



##
# setting baseline report content
##
content = {
    'openness':{'high':'You scored high on Openness to Experience. People who score high on this trait are more likely to seek out a variety of experiences, be more comfortable with the uncertainty, exhibit high levels of curiosity, enjoy being surprised, and pay attention to their inner feelings more than those who are lower on the trait.',
               'medium':'You scored at a medium level on Openness to Experience. People who score at a medium level on Openness to Experience like routine but are not opposed to trying new things, enjoy both facts and fantasy, have some interest in art, are aware of their emotions and feelings, are more adventurous, and are more willing to break with rules or traditions, than lower scorers.',
               'low':'You scored low on Openness to Experience. People who score at a low level on Openness to Experience prefer consistency and caution, tend to be pragmatic and data-driven, and are more resistant to change, relative to score high on Openness to Experience.'},
    'extraversion':{'high':'You scored high on Extraversion. People who score high on this trait enjoy excitement and are enthusiastic, energetic, talkative, and assertive.',
                        'medium':'You scored at a medium level on Extraversion. People who score at a medium level on this trait are neither social butterflies nor wallflowers. They enjoy the time they spend with others but they also enjoy their time alone. They have medium levels of friendliness, cheerfulness, assertiveness, activity, and excitement seeking.',
                        'low':'You scored lower on Extraversion. People who are low in extraversion are less outgoing and more comfortable working by themselves. They may be less involved in social activities, and tend to be quiet and introverted. '},
    'conscientiousness':{'high':'You scored high on Conscientiousness. People who score high on this trait are reliable and prompt, good at making and achieving long-term goals, and are very hardworking. ',
                        'medium':'You scored at a medium level on Conscientiousness. People who score at a medium level on this trait are fairly reliable, organized, orderly, cautious, and self-disciplined. ',
                        'low':'You scored lower on conscientiousness. People who are lower on conscientiousness tend to be more comfortable taking risks and more flexible about meeting deadlines. '},
    'agreeableness':{'high':'You scored high on Agreeableness. People who score high on this trait highly value getting along with others and are willing to put aside their own interests for those of others. They tend to be more helpful, friendly, considerate, and generous to others. ',
                        'medium':'You scored at a medium level on Agreeableness.  People who score at a medium level on this trait try to balance a concern for others’ needs with their own. They tend to be trusting of others, cooperate in relationships, modest, and sympathetic. ',
                        'low':'You scored lower on agreeableness. People with low levels of agreeableness are more inclined to follow their own path and interests than to go along with others.  '},
    'neuroticism':{'high':'You scored high on Neuroticism. People who score high on this trait are characterised by high levels of concern, which at times might even be experienced as stress or anxiety. ',
                        'medium':'You scored at a medium level on Neuroticism. People who score at a medium level on this trait experience a typical level of distress and anxiety in the face of stressful situations. ',
                        'low':'You scored low on Neuroticism. People with low levels of neuroticism find it easier to remain calm and poised in the face of stressful situations. '}
}

for b5 in content:
    for level in content[b5]:
        words = re.findall(re.compile('[^ ]+'),content[b5][level])
        i = 6
        while i < len(words):
            words.insert(i, '\n')
            i += 7
        sentence = ' '.join(word for word in words)
        sentence = re.sub('\n ','\n',sentence)
        content[b5][level] = sentence

##
# End
##



###
# generating report and downloading to folder
###
df = score_df

# Generically define how many plots along and across
for p in range(len(df)):
        
    #clearing figure from memory if applicable
    try:
        del fig
    except:
        pass
        
    try:
        del axes
    except:
        pass
        
    
    try:
        ncols = 2
        nrows = 5  # int(np.ceil(len(df.columns) / (1*ncols)))
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, 30))

        counter = 0
        plt.style.use('fivethirtyeight')
        for i in range(nrows):
            for j in range(ncols):
                ax = axes[i][j]
                ax.set_frame_on(False)
                # Plot when we have data
                if counter % 2 == 0:

                    color = ((counter // 2 + 1) / 5, (1 - (counter // 2 + 1) / 5), (1 - ((counter // 2) / 5)) ** .5)

                    ax.plot(np.arange(-3, 3, .1), [norm.pdf(x, 0, 1) for x in np.arange(-3, 3, .1)], lw=6, alpha=1, color=color)
                    ax.fill_between(np.arange(-3, -.9, .1), [norm.pdf(x, 0, 1) for x in np.arange(-3, -.9, .1)], y2=0,
                                    alpha=.15, color=color)
                    ax.fill_between(np.arange(-1, 1.1, .1), [norm.pdf(x, 0, 1) for x in np.arange(-1, 1.1, .1)], y2=0, alpha=.5,
                                    color=color)
                    ax.fill_between(np.arange(1, 3, .1), [norm.pdf(x, 0, 1) for x in np.arange(1, 3, .1)], y2=0, alpha=.85,
                                    color=color)

                    zscore = (df.iloc[p][df.columns[counter // 2]] - distributions[df.columns[counter // 2]][0]) / \
                             distributions[df.columns[counter // 2]][1]

                    if zscore < -2.9:
                        zscore = -2.9

                    if zscore > 2.9:
                        zscore = 2.9

                    ax.bar([zscore], [.5], color=(.2, .1, .4), width=.05, label='Your Score')

                    ax.set_xlim([-3, 3])
                    ax.set_title(categories[counter // 2], size=20, rotation=0)
                    ax.set_yticks([])
                    ax.set_ylim([-.05, .7])
                    # ax.set_xticks()
                    leg = ax.legend(loc='upper left')
                    leg.draw_frame(True)
                    ax.grid(False)

                    ax2 = ax.twiny()
                    ax2.xaxis.set_ticks_position("bottom")
                    ax2.xaxis.set_label_position("bottom")
                    ax2.spines["bottom"].set_position(("axes", -0.15))
                    ax2.set_xticks([-2.5, 0, 2.5])
                    ax2.set_xticklabels(['Low', '-Level-', 'High'])
                    ax2.grid(False)


                elif counter % 2 == 1:
                    zscore = (df.iloc[p][df.columns[counter // 2]] - distributions[df.columns[counter // 2]][0]) / \
                             distributions[df.columns[counter // 2]][1]

                    if zscore < -1:
                        c = content[df.columns[counter // 2].lower()]['low']
                    elif zscore > 1:
                        c = content[df.columns[counter // 2].lower()]['high']
                    else:
                        c = content[df.columns[counter // 2].lower()]['medium']

                    ax.grid(False)
                    ax.set_yticks([])
                    ax.set_xticks([])
                    ax.text(0, .4 - len(c) / 1000, c, fontsize=20)

                    # Remove axis when we no longer have data
                else:
                    ax.set_axis_off()

                counter += 1
        try:
            try:
                print(WaldmanIDs[df.index[p]],names[df.index[p]],emails[df.index[p]],df.index[p])
            except:
                print('error!',df.index[p])
            fig.suptitle('\nYour Personality Report: {}'.format(names[df.index[p]]), fontsize=50, fontstyle='normal')
            fig.text(.025, .025, 'Report generated on {}'.format(time),fontsize=20)
            fig.text(.5, .025, 'Behavior Genetics of Personality and Behavior Lab - Emory University',fontsize=20)
            fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=.75)
            
            fig.savefig('downloaded\{}_{}_{}_{}.png'.format(WaldmanIDs[df.index[p]],names[df.index[p]],emails[df.index[p]],df.index[p]))
            plt.close()
        except:
            print('error2',df.index[p])
            pass
    except:
        print('error1',df.index[p])
        pass
#plt.show()