#import module
import streamlit as st
import pandas as pd
import re
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from mlxtend.preprocessing import TransactionEncoder
te = TransactionEncoder()
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.frequent_patterns import association_rules
from streamlit_agraph import agraph, Node, Edge, Config
import nltk
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

#===config===
st.set_page_config(
     page_title="Coconut",
     page_icon="🥥",
     layout="wide"
)
st.header("Biderected Keywords Network")
st.subheader('Put your CSV file here ...')

#===Read data===
uploaded_file = st.file_uploader("Choose a file")

col1, col2 = st.columns(2)
with col1:
    method = st.selectbox(
         'Choose method',
       ('Stemming', 'Lemmatization'))
with col2:
    keyword = st.selectbox(
        'Choose column',
       ('Author Keywords', 'Index Keywords'))


#===body=== 
if uploaded_file is not None:
    papers = pd.read_csv(uploaded_file)
    arul = papers.dropna(subset=[keyword])
     
    arul[keyword] = arul[keyword].map(lambda x: re.sub('-—–', ' ', x))
    arul[keyword] = arul[keyword].map(lambda x: re.sub('; ', ' ; ', x))
    arul[keyword] = arul[keyword].map(lambda x: x.lower())
    arul[keyword] = arul[keyword].dropna()
        
    #===stem/lem===
    if method is 'Lemmatization':          
        lemmatizer = WordNetLemmatizer()
        def lemmatize_words(text):
             words = text.split()
             words = [lemmatizer.lemmatize(word) for word in words]
             return ' '.join(words)
        arul[keyword] = arul[keyword].apply(lemmatize_words)
             
    else:
        stemmer = SnowballStemmer("english")
        def stem_words(text):
            words = text.split()
            words = [stemmer.stem(word) for word in words]
            return ' '.join(words)
        arul[keyword] = arul[keyword].apply(stem_words)
    
    arule = arul[keyword].str.split(' ; ')
    arule_list = arule.values.tolist()
         
    te_ary = te.fit(arule_list).transform(arule_list)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    
col1, col2, col3 = st.columns(3)
with col1:
    supp = st.slider(
        'Select value of Support',
        0.001, 1.000, (0.040))
with col2:
    conf = st.slider(
        'Select value of Confidence',
        0.001, 1.000, (0.070))
with col3:
    maxlen = st.slider(
        'Maximum length of the itemsets generated',
        2, 8, (2))

#===Association rules===
if uploaded_file is not None: 
    freq_item = fpgrowth(df, min_support=supp, use_colnames=True, max_len=maxlen)
    if freq_item.empty:
          st.error('Please lower your value.', icon="🚨")
    else:
         res = association_rules(freq_item, metric='confidence', min_threshold=conf) 
         #res = res[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
         res['antecedents'] = res['antecedents'].apply(lambda x: ', '.join(list(x))).astype('unicode')
         res['consequents'] = res['consequents'].apply(lambda x: ', '.join(list(x))).astype('unicode')
         st.dataframe(res, use_container_width=True)
               
         #===visualize===
            
         if st.button('📈 Generate network visualization'):
             with st.spinner('Visualizing, please wait ....'): 
                 res['to'] = res['antecedents'] + ' → ' + res['consequents'] + '\n Support = ' +  res['support'].astype(str) + '\n Confidence = ' +  res['confidence'].astype(str) + '\n Conviction = ' +  res['conviction'].astype(str)
                 res_node=pd.concat([res['antecedents'],res['consequents']])
                 res_node = res_node.drop_duplicates(keep='first')

                 nodes = []
                 edges = []

                 for x in res_node:
                     nodes.append( Node(id=x, 
                                    label=x,
                                    size=10,
                                    shape="circularImage",
                                    labelHighlightBold=True,
                                    group=x,
                                    opacity=10,
                                    mass=1,
                                    image="https://upload.wikimedia.org/wikipedia/commons/f/f1/Eo_circle_yellow_circle.svg") 
                             )   

                 for y,z,a,b in zip(res['antecedents'],res['consequents'],res['confidence'],res['to']):
                     edges.append( Edge(source=y, 
                                     target=z,
                                     title=b,
                                     width=a*2,
                                     physics=True,
                                     smooth=True
                                     ) 
                             )  

                 config = Config(width=1200,
                                 height=800,
                                 directed=True, 
                                 physics=True, 
                                 hierarchical=False,
                                 maxVelocity=5
                                 )

                 return_value = agraph(nodes=nodes, 
                                       edges=edges, 
                                       config=config)