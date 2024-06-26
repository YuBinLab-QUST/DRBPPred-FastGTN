import numpy as np
import pandas as pd
from sklearn.preprocessing import scale,StandardScaler 
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import roc_curve, auc
from sklearn.model_selection import StratifiedKFold
# import keras.utils.np_utils as utils
# import utils.tools as utils
import utils.tools as utils
# from tensorflow.keras.utils import to_categorical
from sklearn.tree import DecisionTreeClassifier
# import tools as utils
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, precision_score, recall_score, roc_auc_score, average_precision_score
def get_shuffle(dataset,label):    
    index = [i for i in range(len(label))]
    np.random.shuffle(index)
    dataset = dataset[index]
    label = label[index]
    return dataset,label  


data_=pd.read_csv(r'')
data1=np.array(data_)
data=data1[:,:]
[m1,n1]=np.shape(data)
# label1=np.ones((int(3846),1))
label1=np.ones((int(2616),1))
label2=np.zeros((int(4175),1))

# label1=np.ones((int(7129),1))
# label2=np.zeros((int(7060),1))
label=np.append(label1,label2)
shu=data
X,y=get_shuffle(shu,label)
sepscores = []
ytest=np.ones((1,2))*0.5
yscore=np.ones((1,2))*0.5
base_tree = DecisionTreeClassifier(max_depth=5)

# Configure AdaBoost with 500 base estimators
# n_estimators = 500
# cv_clf = AdaBoostClassifier(base_estimator=base_tree, n_estimators=n_estimators)
cv_clf = AdaBoostClassifier()
skf= StratifiedKFold(n_splits=10)
ytest=np.ones((1,2))*0.5
yscore=np.ones((1,2))*0.5
for train, test in skf.split(X,y): 
    y_train=utils.to_categorical(y[train])
    hist=cv_clf.fit(X[train], y[train])
    y_score=cv_clf.predict_proba(X[test])
    yscore=np.vstack((yscore,y_score))
    y_test=utils.to_categorical(y[test])
    ytest=np.vstack((ytest,y_test))
    fpr, tpr, _ = roc_curve(y_test[:,0], y_score[:,0])
    roc_auc = auc(fpr, tpr)
    # y_class= utils.categorical_probas_to_classes(y_score)
    y_class = np.argmax(y_score, axis=1)
    # y_class=utils.probas_to_classes(y_score)
    y_test_tmp=y[test]
    acc, precision,npv, sensitivity, specificity, mcc,f1 = utils.calculate_performace(len(y_class), y_class, y_test_tmp)
    aupr = average_precision_score(y_test[:,0], y_score[:,0])
    sepscores.append([acc, precision,npv, sensitivity, specificity, mcc,f1,roc_auc,aupr])
    print('Ada:acc=%f,precision=%f,npv=%f,sensitivity=%f,specificity=%f,mcc=%f,f1=%f,roc_auc=%f,aupr=%f'
          % (acc, precision,npv, sensitivity, specificity, mcc,f1, roc_auc,aupr))
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
row=yscore.shape[0]
yscore=yscore[np.array(range(1,row)),:]
yscore_sum = pd.DataFrame(data=yscore)
yscore_sum.to_csv('')
ytest=ytest[np.array(range(1,row)),:]
ytest_sum = pd.DataFrame(data=ytest)
ytest_sum.to_csv('')
print(ytest[:,0])
print(yscore[:,0])
fpr, tpr, _ = roc_curve(ytest[:,0], yscore[:,0])
auc_score=np.mean(scores, axis=0)[7]
lw=2
plt.plot(fpr, tpr, color='darkorange',
lw=lw, label='Ada ROC (area = %0.2f%%)' % auc_score)
plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
plt.xlim([0.0, 1.05])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")
plt.show()
data_csv = pd.DataFrame(data=result)
colum = ['ACC', 'precision', 'npv', 'Sn', 'Sp','MCC','F1','AUC']
ro=['1', '2', '3','4','5','6','7','8','9','10','11']  
data_csv.to_csv('')
