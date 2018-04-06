import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.core.display import display, HTML

# define function that computes percentiles for multiple columns
def percentiles(DF, columns, groups=None):
    df = DF.copy()
    if groups==None:
        for i in columns:
            df[i] = df[i].rank(pct=True)
    elif groups in df: 
        df = df.groupby(groups, as_index=False).apply(lambda data: percentiles(data, columns))
    else: 
        df = df.groupby(level=groups, as_index=False).apply(lambda data: percentiles(data, columns))
 
    return df

def ranking(DF, col_to_rank="", rename_col_dict=False):
    irsregion = pd.read_csv('../data/partner_irsregion.csv', index_col='Partner Details Partner ID')# Merge IRS Region to ISC
    #     print ISC.merge(irsregion['Loan Geography IRS Region'],  how='outer', right_on='Partner Details Partner ID', left_index=True).head()
    DF = DF.merge(irsregion[['Loan Geography IRS Region', 'Partner Details Field Partner Name']],  how='outer', left_index=True, right_index=True)

    pctscores = percentiles(DF, col_to_rank)
    region_pctscores = percentiles(pctscores, col_to_rank, groups='Loan Geography IRS Region').reset_index(level=0, drop=True)
    DF = DF.join(pctscores[col_to_rank], rsuffix=' pct').join(region_pctscores[col_to_rank], rsuffix=' region pct')
    DF.drop_duplicates(inplace=True)

    if rename_col_dict:
        DF.rename(columns = rename_col_dict,inplace=True)
    return DF

def PartnerName(df, partnerid, html = False, text=False):
    NAME = df.loc[partnerid, 'Name']
    partnername = "<h1>Kiva's Impact Reportcard for <em>{}</em></h1>".format(NAME)
    if text: return NAME
    elif html: return partnername
    else: return HTML(partnername)
    
def TableDescription():
    Description = "<br><h2>Table description</h2></br><br>The table in this report shows the median of all partners, and describes how well this partner scores in comparison to all partners and to partners in the same region.</br><br><b>For example: </b>A comparison score of 0.8 means that this partner scores higher than 80% of all partners, or all partners in the same region.</br>"
    return HTML(Description)
    
def ComponentSummary(df, partnerid="", component="", html=False, table="",image = ""):
    """Fill in partner id, impact score card component ('Impact', 'Targeting', 'Product'), and subcomponent as True or False."""
    
    V = {}
    V['component_value'] = round(df.loc[partnerid,component],1)
    V['component_median'] = round(df.loc[:,component].median(),1)
    V['component'] = component
    V['table'] = table
    V['image'] = image
    Title  = "<h2>{component} Score: {component_value}/10 <small>(Median {component_median}/10)</small></h2>".format(**V)

    if component == 'Impact':
            Summary = "The Impact Score is built on three subcomponent scores:\
            <br>The <b>Targeting score</b> (measuring how much we think a partner's clients need financial services),\
            <br>The <b>Product score</b> (measuring the impactfulness of the loans being offered),\
            <br>and the <b>Process score</b> (measuring the quality of a partner's operations and M&E system).".format(**V)

    if component == 'Targeting':
            Summary = "The Targeting Score measures how underserved the borrowers of the partner are, based on three components.\
            <br>The <b>MPI Score</b> measures the poverty level on a subnational level, accounting for the portion of a partner's portfolio in rural areas.\
            <br>The <b>Findex Score</b> measures the rate of account ownership and borrowing in the country.\
            <br>Finally, the <b>Outreach Score</b> measures the portion of borrowers in a variety of high-priority or frequently financially excluded groups.".format(**V)
    
    if component == 'Product':
            Summary = "The Product Score measures how valuable we expect a partner's financial services to be to borrowers, given the evidence in our sector research page.\
            <br>This is mostly based on the <b>Research Score</b>, which measures the degree of research support for the reporting tags assigned to partners' loan themes.\
            <br>Some loan themes also get a <b>Sector Score</b>, which defines Kiva's broad sector-level priorities.".format(**V)
    
    if component == 'Process':
                Summary = "The Process Score evaluates how client-centric a partner's operations are, including the level of nuance in their M&E systems, the appropriateness of their MIS system, and subjective assessments of price fairness and transparency.\
                <br>(NOTE: The underlying data here is still being collected, so for now we report the old process scores).".format(**V)

    if html: return Title,Summary
    else:
        Summary = Title+Summary
        return HTML(Summary)    
    
def ScoringTable(df, partnerid, component="", region=True, html = False):
    """Fill in ISC dataframe, partnerid, impact component, where component is 'Impact', 'Targeting', 'Product', 'Process'. 
    For component='Impact' returns the highest level impact scores."""

    if component == 'Impact': components = ['Impact', 'Targeting', 'Product','Process']
    elif component == 'Targeting': components = ['Targeting', 'MPI', 'Findex', 'Outreach']
    elif component == 'Product': components = ['Product', 'Research', 'Sector']
    elif component == 'Process': components = ['Process']
        
    d = {'Component': components}
    region_name = df.loc[partnerid, 'Loan Geography IRS Region']
    region_ISOs = {"Central America and the Caribbean" : "LAC",
                   "East Asia and the Pacific" : "EAP",
                   "Europe (Including Iceland and Greenland)" : "W. Europe",
                   "Middle East and North Africa" : "ME/NA",
                   "North America" : "Mexico",
                   "Russia and the Newly Independent States" : "E. Europe",
                   "South America" : "S. Amer",
                   "South Asia" : "S. Asia",
                   "Sub-Saharan Africa" : "SSA"
                                }

    region_ISO = region_ISOs.get(region_name)

    pct = lambda val: "{}%".format(round(100*df.loc[partnerid,val],1))
    for C in components:
        d.setdefault('Component Score',[]).append(round(df.loc[partnerid,C],2))
        d.setdefault('Percentile (vs. All)',[]).append(pct('{} pct'.format(C)))
        d.setdefault('Percentile (vs. {})'.format(region_ISO),[]).append(pct('{} region pct'.format(C)))
        d.setdefault('Median (All)',[]).append(round(df['{}'.format(C)].median(),2))
        if region:
           df = df.loc[df['Loan Geography IRS Region']==region_name,:]
           d.setdefault('Median ({})'.format(region_ISO),[]).append(round(df['{}'.format(C)].median(),2))
    df = pd.DataFrame(d).set_index('Component')
    df = df[['Component Score', 'Median (All)', 'Percentile (vs. All)', 'Median ({})'.format(region_ISO), 'Percentile (vs. {})'.format(region_ISO)]]
    if html: return df.to_html()
    else: return df 

def ComponentHist(df, partnerid = False, component="", region = False, ax = None, saveas=""):        
    if ax is None: fig,ax = plt.subplots()
    if region:
        region_name = df.loc[partnerid, 'Loan Geography IRS Region']
        df = df.loc[df['Loan Geography IRS Region']==region_name,:]
        title = "{} Score Distribution for all partners in {}".format(component, region_name)
    else:
        title = "{} Score Distribution for all partners".format(component)        
    df[component].plot(kind='hist', title=title, ax=ax, figsize=(10,5)) # bins=11
    ax.set_xlabel(component)

    if partnerid:
        partnername = df.loc[partnerid,'Name']
        title = "{}'s place in the ".format(partnername) + title
        low,high = ax.get_ylim()
        ax.vlines(df.loc[partnerid, component], low, high, colors='green', linewidth=4)
    plt.tight_layout()

    if saveas: plt.savefig(saveas)
    return ax 

def bothHistograms(df, partnerid = False, component="", region = False, ax = None, saveas="", html=True):
    """
    Make a figure with both histograms
    """
    fig, ax = plt.subplots(1, 2)
    ComponentHist(df, partnerid = partnerid, component=component, region = False, ax = ax[0], saveas=False)
    ComponentHist(df, partnerid = partnerid, component=component, region = True,  ax = ax[1], saveas=False)
    if saveas: plt.savefig(saveas)
    if html:
        return "<p><img src='../figures/{0}_{1}.png' alt='{1} Histograms' height='330' width='800'/></p>".format(partnerid,component)
        plt.close(fig)
        plt.clf()
    else: return fig,ax
    
def LoanThemes(df, partnerid):
    df = df.loc[partnerid]
    df.drop('Loan Theme Type', axis=1, inplace=True)
    return df
    
def CountofResearchRating(LoanThemes, df, partnerid):
    count = LoanThemes(df, partnerid).groupby('Research Rating').size().to_frame()
    count.columns = ['count']
    return count

partner_loanthemes_reportingtags = '../data/partner_loanthemes_reportingtags.csv'
lt = pd.read_csv(partner_loanthemes_reportingtags, usecols=['Partner ID', 'Loan Theme Type: Loan Theme Type Name', 'Loan Theme Name', 'Reporting Tag: Reporting Tag Name', 'Research Rating'], index_col='Partner ID', encoding = "ISO-8859-1")
columnnames = {'Loan Theme Type: Loan Theme Type Name': 'Loan Theme Type', 'Reporting Tag: Reporting Tag Name': 'Reporting Tag'}
lt.rename(columns = columnnames, inplace=True)
lt.dropna(inplace=True)
lt.index = lt.index.astype(int)

def ISCdata(datafile = '../scores/ISC_components.csv'):
    """
    Make ISC data
    """
    
    ISC_scores = datafile
    ISC = pd.read_csv(ISC_scores, index_col=0, encoding = "ISO-8859-1")
    list_col_to_rank = ['Impact','Targeting','Product', 'Process', 'MPI','Findex', 'Outreach', 'Research', 'Sector']
    ISC = ranking(ISC, list_col_to_rank)
    return ISC
 
def write_reportcard(partnerid = 202, template = "./Template.htm", css = "./Template.css",saveas = ""):

    ISC = ISCdata()
   
    #~ Make template values
    report = {}
    report['PartnerName'] = PartnerName(ISC, partnerid,html=True)
    report['NAME']        = PartnerName(ISC, partnerid, text=True)
    report['PartnerStats']= "{} is a Kiva field partner in {} with ${} in volume funded over the past 18 months.".format(ISC.loc[partnerid,"Name"],ISC.loc[partnerid,"Country"],round(ISC.loc[partnerid,"volume"],0))
    with open(css,'r') as CSS: report['Stylesheet']  = CSS.read()
    
    for C in ['Impact', 'Targeting', 'Product', 'Process']:
        report['{}Table'.format(C)] = ScoringTable(ISC, partnerid, C, html=True)
        img_path = "{}_{}.png".format(partnerid,C)
        img_link = bothHistograms(ISC, partnerid, C,saveas = "./figures/"+img_path)
        report['{}Histograms'.format(C)] = img_link
        report['{}Title'.format(C)],report['{}Text'.format(C)] = ComponentSummary(ISC,partnerid,C,html=True)

    if saveas:
        TEMPLATE = open(template,'r')
        ReportFile = open(saveas,'w')
        ReportFile.write(TEMPLATE.read().format(**report))
        TEMPLATE.close()
        ReportFile.close()
            
    return report
        
def main(partnerid=202, verbose=True):
    ISC = ISCdata().groupby(level=0).first()
    NAME = PartnerName(ISC, partnerid, text=True).replace(" ","")
    if verbose: print(NAME)
    write_reportcard(partnerid,saveas="./PartnerReports/{}.html".format(NAME))
    #~ os.system("pandoc -o ./PartnerReports/{name}.html -f markdown_strict -t html ./PartnerReports/{name}.md".format(name=NAME))
    return ISC

if __name__ == '__main__':
    if len(sys.argv)>1: IDs = [int(i) for i in sys.argv[1:]]
    else: 
        IDs = [202, 386, 77, 55, 58]
    for ID in IDs: 
        try: ISC = main(ID)
        except: print("Something went wrong with ID {}".format(ID))

