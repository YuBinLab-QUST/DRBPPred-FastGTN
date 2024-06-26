
import math
import pandas as pd
import numpy as np
from sklearn.preprocessing import scale
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_curve, auc
from keras.layers import Input, Dense
from keras.layers import BatchNormalization
from keras.layers import LeakyReLU
from keras.models import Sequential, Model
from keras.optimizers import Adam
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, precision_score, recall_score, roc_auc_score, average_precision_score
def get_shuffle(dataset,label):    
    index = [i for i in range(len(label))]
    np.random.shuffle(index)
    dataset = dataset[index]
    label = label[index]
    return dataset,label  
data_start = pd.read_csv("")
# label_P=np.ones((int(7129),1)) 
# label_N=np.zeros((int(7060),1))
label_P=np.ones((int(2616),1)) 
label_N=np.zeros((int(4175),1))
label_start=np.append(label_P,label_N)
# label_start = np.hstack((label_P,label_N))
label=np.array(label_start)
data=np.array(data_start)
shu1=data
shu2,y=get_shuffle(shu1,label)
shu=scale(shu2)


[sample_num,input_dimwx]=np.shape(shu)
# X = np.reshape(shu,(-1,1,input_dimwx))
X = shu

optimizer = Adam(1e-5, 0.5)
n_y_value = 2

D = Sequential()
D.add(Dense(1024))
D.add(LeakyReLU(alpha=0.2))
# D.add(Dense(512))
D.add(Dense(2, activation='sigmoid'))
img = Input(shape=(n_y_value,))
validity = D(img)
Discriminator = Model(img,validity)
Discriminator.compile(loss='categorical_crossentropy',
            optimizer=optimizer,
            metrics=['accuracy'])



N_ideas = input_dimwx
G = Sequential()
G.add(Dense(8,input_dim=N_ideas))
G.add(LeakyReLU(alpha=0.2))
G.add(BatchNormalization(momentum=0.8))
# G.add(Dense(32))
# G.add(LeakyReLU(alpha=0.2))
# G.add(BatchNormalization(momentum=0.8))
# G.add(Dense(32))
# G.add(LeakyReLU(alpha=0.2))
# G.add(BatchNormalization(momentum=0.8))
G.add(Dense(n_y_value, activation='relu'))
noise = Input(shape=(N_ideas,))
G_img = G(noise)
Generator = Model(noise,G_img)

z = Input(shape=(N_ideas,))
G_img = Generator(z)
Discriminator.trainable = False
validity = Discriminator(G_img)
GAN = Model(z,validity)
GAN.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics =['accuracy'])

def categorical_probas_to_classes(p):
    return np.argmax(p, axis=1)


def to_categorical(y, nb_classes=None):
    y = np.array(y, dtype='int')
    if not nb_classes:
        nb_classes = np.max(y)+1
    Y = np.zeros((len(y), nb_classes))
    for i in range(len(y)):
        Y[i, y[i]] = 1
    return Y


def get_shuffle(data, label):
    index = [i for i in range(len(label))]
    np.random.shuffle(index)
    data = data[index]
    label = label[index]
    return data, label


def calculate_performace(test_num, pred_y,  labels):
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    for index in range(test_num):
        if labels[index] == 1:
            if labels[index] == pred_y[index]:
                tp = tp + 1
            else:
                fn = fn + 1
        else:
            if labels[index] == pred_y[index]:
                tn = tn + 1
            else:
                fp = fp + 1

    acc = float(tp + tn)/test_num
    precision = float(tp)/(tp + fp + 1e-06)
    npv = float(tn)/(tn + fn + 1e-06)
    sensitivity = float(tp) / (tp + fn + 1e-06)
    specificity = float(tn)/(tn + fp + 1e-06)
    mcc = float(tp*tn-fp*fn) / \
        (math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)) + 1e-06)
    f1 = float(tp*2)/(tp*2+fp+fn+1e-06)
    return acc, precision, npv, sensitivity, specificity, mcc, f1

sepscores = []
ytest=np.ones((1,2))*0.5
yscore=np.ones((1,2))*0.5

skf= StratifiedKFold(n_splits=5)

for train, test in skf.split(X,y): 

    y_train=to_categorical(y[train])#generate the resonable results
    cv_clf = GAN
    hist = cv_clf.fit(X[train], 
                    y_train,
                    epochs=30)
    y_test=to_categorical(y[test])#generate the test 
    ytest=np.vstack((ytest,y_test))
    y_test_tmp=y[test]       
    y_score=cv_clf.predict(X[test])#the output of  probability
    yscore=np.vstack((yscore,y_score))
    fpr, tpr, _ = roc_curve(y_test[:,0], y_score[:,0])
    roc_auc = auc(fpr, tpr)
    y_class= categorical_probas_to_classes(y_score)
    aupr = average_precision_score(y_test[:,0], y_score[:,0])
    acc, precision,npv, sensitivity, specificity, mcc,f1 = calculate_performace(len(y_class), y_class, y_test_tmp)
    sepscores.append([acc, precision,npv, sensitivity, specificity, mcc,f1,roc_auc,aupr])
    print('Results: acc=%f,precision=%f,npv=%f,sensitivity=%f,specificity=%f,mcc=%f,f1=%f,roc_auc=%f,aupr=%f'
          % (acc, precision,npv, sensitivity, specificity, mcc,f1, roc_auc,aupr))
    cv_clf=[]
    hist=[]
    # hist=[]
    # cv_clf=[]
scores=np.array(sepscores)
print("acc=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[0]*100,np.std(scores, axis=0)[0]*100))
print("precision=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[1]*100,np.std(scores, axis=0)[1]*100))
print("npv=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[2]*100,np.std(scores, axis=0)[2]*100))
print("sensitivity=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[3]*100,np.std(scores, axis=0)[3]*100))
print("specificity=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[4]*100,np.std(scores, axis=0)[4]*100))
print("mcc=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[5]*100,np.std(scores, axis=0)[5]*100))
print("f1=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[6]*100,np.std(scores, axis=0)[6]*100))
print("roc_auc=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[7]*100,np.std(scores, axis=0)[7]*100))
print("aupr=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[8]*100,np.std(scores, axis=0)[8]*100))
result1=np.mean(scores,axis=0)
H1=result1.tolist()
sepscores.append(H1)

result=sepscores
data_csv_zhibiao = pd.DataFrame(data=result)
row=yscore.shape[0]
yscore=yscore[np.array(range(1,row)),:]
yscore_sum = pd.DataFrame(data=yscore)

ytest=ytest[np.array(range(1,row)),:]
ytest_sum = pd.DataFrame(data=ytest)

data_csv_zhibiao.to_csv('')
yscore_sum.to_csv('')
ytest_sum.to_csv('')
