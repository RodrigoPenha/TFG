#import graph
import os
import numpy as np



import random
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsClassifier 
from sklearn import svm

def tot_edges(g):
    '''Returns the total number of edges for undirected graphs
    '''
    return sum([sum(el) for el in g])/2

def edit_distance(g_1,g_2):
    '''
    '''
    return tot_edges(abs(g_1-g_2))

def create_graph(g,t):
    '''
    '''
    dim = len(g)
    distribution = []
    for i in range(0,dim):
        for j in range(i+1,dim):
            el = abs(g[i][j])
            distribution.append(el)
    distribution.sort()
    p = np.percentile(distribution,t)
    g_new = np.zeros((dim,dim))
    for i in range(0,dim):
        for j in range(i+1,dim):
            if abs(g[i][j])>=p:
                g_new[i][j]=1
                g_new[j][i]=1
    return g_new

def preprocessing_g(g,p_low,p_high):
    '''
    '''
    dim = len(g)
    distribution = []
    for i in range(0,dim):
        for j in range(i+1,dim):
            el = g[i][j]
            distribution.append(el)
    distribution.sort()
    p_min = np.percentile(distribution,p_low)
    p_max = np.percentile(distribution,p_high)
    print(p_min,p_max)
    g_new = np.zeros((dim,dim))
    for i in range(0,dim):
        for j in range(i+1,dim):
            if g[i][j]>p_max or g[i][j]<p_min:
                g_new[i][j]=1
                g_new[j][i]=1
    return g_new

def create_graph2(g,t):
    '''
    '''
    dim = len(g)
    distribution = []
    for i in range(0,dim):
        for j in range(i+1,dim):
            el = g[i][j]
            distribution.append(el)
    distribution.sort()
    p = np.percentile(distribution,t)
    g_new = np.zeros((dim,dim))
    for i in range(0,dim):
        for j in range(i+1,dim):
            if g[i][j]>=p:
                g_new[i][j]=1
                g_new[j][i]=1
    return g_new



def coeff_ab(g,td_asd,asd_td):
    '''
    '''
    # create the induced subgraph
    def sub_graph(g,v_sub,verbose=False):
        '''To generate the sub graph
        '''
        g_sub = np.copy(g)
        l_1 = [el for el in v_sub]
        g_sub = g_sub[np.ix_(l_1,l_1)]
        return g_sub
    
    # Induce the sub-graphs
    g_td_asd = sub_graph(g,td_asd)
    g_asd_td = sub_graph(g,asd_td)

    # Coefficients
    a = sum([sum(i) for i in g_td_asd])/2
    b = sum([sum(i) for i in g_asd_td])/2

    return a,b

# cambiar el path al directorio del archivo
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def classifiers(x_train,y_train,x_test,y_test):
    '''
    '''
    results_i = []
    models = []
    
    # KNN
    training_accuracy = [] 
    test_accuracy = []
    kn_models = []
    neighbors_settings = range(1, 30)
    for n_neighbors in neighbors_settings:
        # build the model
        clf = KNeighborsClassifier(n_neighbors=n_neighbors) 
        clf.fit(x_train, y_train)
        # record training set accuracy 
        training_accuracy.append(clf.score(x_train, y_train)) 
        # record generalization accuracy 
        scc = clf.score(x_test, y_test)
        test_accuracy.append(scc)
        kn_models.append(clf)
    kn = test_accuracy.index(max(test_accuracy))
    results_i.append(test_accuracy[kn])
    models.append(kn_models[kn])
    
    # SCM
    test_accuracy_svm = []
    clf = svm.SVC(kernel='linear', C = 1.0)
    clf.fit(x_train, y_train)
    results_i.append(clf.score(x_test, y_test))
    models.append(clf)
    
    return results_i,models

 #create the induced subgraph
def sub_graph(g,v_sub):
    '''To create the sub graph og 'g' from the list of nodes in 'v_sub'.
    '''
    g_sub = np.copy(g)
    #l_1 = [el for el in v_sub]
    l_1 = [el for el in v_sub]
    g_sub = g_sub[np.ix_(l_1,l_1)]
    return g_sub

def oracle(g, clf):
    ''' The classification funcion for the graph 'g'
    '''
    # Sub-graphs
    td_adhd = [130, 4, 133, 6, 136, 140, 13, 144, 17, 18, 19, 151, 132, 26, 27, 167, 30, 159, 161, 162, 155, 36, 37, 38, 39, 170, 43, 172, 175, 48, 177, 178, 180, 158, 183, 56, 57, 60, 61, 62, 67, 69, 70, 73, 76, 78, 141, 85, 86, 176, 91, 92, 94, 100, 105, 107, 108, 112, 114, 116, 120, 121, 124, 126, 127]
    adhd_td = [128, 1, 2, 150, 134, 7, 11, 15, 145, 146, 147, 22, 151, 156, 32, 33, 35, 164, 163, 166, 40, 169, 42, 171, 173, 46, 47, 177, 50, 179, 53, 54, 184, 185, 186, 168, 188, 189, 181, 64, 160, 66, 68, 182, 71, 72, 74, 75, 143, 81, 82, 83, 89, 90, 91, 165, 97, 187, 104, 106, 113, 114, 115, 118, 120]
    
    # Line Coefficients
    w_1 = clf.coef_[0][0]
    w_2 = clf.coef_[0][1]
    bk = clf.intercept_[0]
    
    # Induced sub-graphs
    g_td_adhd = sub_graph(g,td_adhd)
    g_adhd_td = sub_graph(g,adhd_td)

    # Coefficients
    a = sum([sum(i) for i in g_td_adhd])/2
    b = sum([sum(i) for i in g_adhd_td])/2

    # Apply the rule
    x = bk + w_1*a + w_2*b
    

    # Classify
    if x>0:
        return 1#,a,b #'ASD'
    else:
        return 0#,a,b#'TD'
    
def oracle_ab(g,clf):
    ''' The classification funcion for the graph 'g' with some information on the classification (a, b parameters)
    '''
    td_adhd = [130, 4, 133, 6, 136, 140, 13, 144, 17, 18, 19, 151, 132, 26, 27, 167, 30, 159, 161, 162, 155, 36, 37, 38, 39, 170, 43, 172, 175, 48, 177, 178, 180, 158, 183, 56, 57, 60, 61, 62, 67, 69, 70, 73, 76, 78, 141, 85, 86, 176, 91, 92, 94, 100, 105, 107, 108, 112, 114, 116, 120, 121, 124, 126, 127]
    adhd_td = [128, 1, 2, 150, 134, 7, 11, 15, 145, 146, 147, 22, 151, 156, 32, 33, 35, 164, 163, 166, 40, 169, 42, 171, 173, 46, 47, 177, 50, 179, 53, 54, 184, 185, 186, 168, 188, 189, 181, 64, 160, 66, 68, 182, 71, 72, 74, 75, 143, 81, 82, 83, 89, 90, 91, 165, 97, 187, 104, 106, 113, 114, 115, 118, 120]
    
    # Line Coefficients
    w_1 = clf.coef_[0][0]
    w_2 = clf.coef_[0][1]
    bk = clf.intercept_[0]
    
    # Induced sub-graphs
    g_td_adhd = sub_graph(g,td_adhd)
    g_adhd_td = sub_graph(g,adhd_td)

    # Coefficients
    a = sum([sum(i) for i in g_td_adhd])/2
    b = sum([sum(i) for i in g_adhd_td])/2

    # Apply the rule
    x = bk + w_1*a + w_2*b

    # Classify
    if x>0:
        return 1 ,a,b #'ASD'
    else:
        return 0,a,b#'TD'


def importgrafos():
    """
    

    Returns
    -------
    graphs : TYPE
        tupla con la etiqueta y el grafo.
    clf : TYPE
        Clasificador entrenado.

    """

    data = {}
    path = '.\\data\\ADHD\\ADHD200_CC200\\'
    i=0
    map_dict = {}
    files = os.listdir(path)
    files = sorted(files)
    for filename in files:
        if 'DS_Store' not in filename:
            with open(path+filename, mode='r') as txt_file: 
                name = filename.split('.')[0]
                file_type = name.split('_')[-3]
                if file_type == 'connectivity':
                    #print(i,' ',name)
                    name = '_'.join(name.split('_')[:-3])
                    lines = txt_file.readlines()
                    m = []
                    for l in lines:
                        m.append([float(el) for el in l.split(' ')])
                    data[name] = np.array(m)
                    map_dict[i] = [name]
                    i+=1
    
    path = '.\\data\\ADHD\\'
    labels_file = 'subject_labels_list.txt'
    labels_l = []
    j=0
    with open(path+labels_file, mode='r') as txt_file:
        lines = txt_file.readlines()
        for l in lines:
            labels_l.append(l)
            if l[0]=='A':
                map_dict[j].append(1)
            else:
                map_dict[j].append(0)
            j+=1
    
    # Put labels with graphs
    for k,v in map_dict.items():
        data[v[0]] = (v[1],data[v[0]])
    
    # Preprocessing
    
    
    
    # BLACK-BOX FUNCTION
    
    adhd_td = [1, 2, 171, 179, 7, 139, 14, 15, 16, 19, 20, 22, 151, 154, 156, 160, 33, 35, 165, 168, 169, 42, 135, 173, 46, 47, 177, 51, 54, 184, 185, 186, 59, 32, 68, 182, 71, 74, 75, 79, 83, 89, 96, 97, 99, 106, 113, 114, 115]
    td_adhd = [1, 130, 132, 6, 7, 11, 12, 13, 18, 21, 152, 153, 30, 161, 162, 35, 134, 38, 167, 41, 170, 43, 174, 175, 178, 180, 158, 187, 62, 63, 65, 69, 70, 71, 76, 77, 80, 82, 84, 85, 86, 92, 94, 100, 101, 102, 105, 108, 117, 122, 124, 126, 127]
    
    
    
    t = 90
    # t1 = 5
    # t2 = 95
    graphs = {}
    tot_edges_list = []
    for k,v in data.items():
        #g = create_graph(v[1],t)
        #g = preprocessing_g(v[1],t1,t2)
        g = create_graph2(v[1],t)
        graphs[k] = (v[0],g)
        tot_edges_list.append(tot_edges(g))
    
    
    ab_list = []
    for k,v in graphs.items():
        name = k
        g = v[1]
        label = v[0]
        a,b = coeff_ab(g,td_adhd,adhd_td)
        ab_list.append((a,b,label))
    
    
    
    
    random.seed(2024)
    yx0 = [(y,[a,b]) for a,b,y in ab_list if y==0]
    yx1 = [(y,[a,b]) for a,b,y in ab_list if y==1]
    random.shuffle(yx0)
    random.shuffle(yx1)
    lenmax = max(len(yx0),len(yx1))
    yx0 = yx0[:lenmax]
    yx1 = yx1[:lenmax]
    yx = yx0 + yx1
    random.shuffle(yx)
    X = np.array([el[1] for el in yx])
    Y = np.array([el[0] for el in yx])
    ##
    kf = KFold(n_splits=5,shuffle=True, random_state=2024)
    kf.get_n_splits(X)
    i = 0
    results = {}
    models_classifier = {}
    for train_index, test_index in kf.split(X):
        train_index = list(train_index)
        test_index = list(test_index)
        #print("TRAIN:", len(train_index), "TEST:", len(test_index))
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = Y[train_index], Y[test_index]
        print(len(X_train),len(X_test),len(y_train),len(y_test))
        #x_train,y_train,x_test,y_test =train_test_sets(,dim_1,dim_2)
        # Classifiers
        results[i],models_classifier[i] = classifiers(X_train,y_train,X_test,y_test)
        i+=1
    
    # Get the best classifier
    clf = models_classifier[3][1]
        
    
    return graphs,clf