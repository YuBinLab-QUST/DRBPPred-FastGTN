import torch
import numpy as np
import torch.nn as nn
from model_gtn import GTN
from model_fastgtn import FastGTNs
import pickle
import argparse
from torch_geometric.utils import  add_self_loops
from sklearn.metrics import f1_score as sk_f1_score
from utils import init_seed, _norm,f1_score
import copy
import pandas as pd
from sklearn.model_selection import StratifiedKFold
import scipy.sparse as sp
from sklearn.neighbors import NearestNeighbors
from torch import Tensor
import dgl
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, precision_score, recall_score, roc_auc_score, average_precision_score
import itertools
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
import pandas as pd
import math 
from scipy import interp
import torch.nn.functional as F
from sklearn.metrics.pairwise import cosine_similarity
import time
time_start = time.time()  # 记录开始时间
# function()   执行的程序


parser = argparse.ArgumentParser()
parser.add_argument('--node_dim', type=int, default=128,
                        help='hidden dimensions')
parser.add_argument('--num_channels', type=int, default=2,
                        help='number of channels')
parser.add_argument('--num_layers', type=int, default=0,
                        help='number of GT/FastGT layers')
parser.add_argument("--channel_agg", type=str, default='concat')
# # Configurations for FastGTNs
parser.add_argument("--non_local", action='store_true', help="use non local operations")
parser.add_argument("--beta", type=float, default=0.5, help="beta (Identity matrix)")
parser.add_argument("--pre_train", action='store_true', help="pre-training FastGT layers")
parser.add_argument('--num_FastGTN_layers', type=int, default=1,
                        help='number of FastGTN layers')

args = parser.parse_args()

def get_shuffle(dataset,label):    
    index = [i for i in range(len(label))]
    np.random.shuffle(index)
    dataset = dataset[index]
    label = label[index]
    return dataset,label  
def calculate_performace(test_num, pred_y,  labels):
    tp =0
    fp = 0
    tn = 0
    fn = 0
    for index in range(test_num):
        if labels[index] ==1:
            if labels[index] == pred_y[index]:
                tp = tp +1
            else:
                fn = fn + 1
        else:
            if labels[index] == pred_y[index]:
                tn = tn +1
            else:
                fp = fp + 1               
            
    acc = float(tp + tn)/test_num
    precision = float(tp)/(tp+ fp + 1e-06)
    npv = float(tn)/(tn + fn + 1e-06)
    sensitivity = float(tp)/ (tp + fn + 1e-06)
    specificity = float(tn)/(tn + fp + 1e-06)
    mcc = float(tp*tn-fp*fn)/(math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)) + 1e-06)
    f1=float(tp*2)/(tp*2+fp+fn+1e-06)
    return acc, precision,npv, sensitivity, specificity, mcc, f1
def to_categorical(y, nb_classes=None):
    '''Convert class vector (integers from 0 to nb_classes)
    to binary class matrix, for use with categorical_crossentropy.
    '''
    y = np.array(y, dtype='int')
    if not nb_classes:
        nb_classes = np.max(y)+1
    Y = np.zeros((len(y), nb_classes))
    for i in range(len(y)):
        Y[i, y[i]] = 1.
    return Y
def categorical_probas_to_classes(p):
    return np.argmax(p, axis=1)

data_=pd.read_csv('')

data1=np.array(data_)
data=data1[:,:]
print(data.shape)
[m1,n1]=np.shape(data)

label1=np.ones((int(7129),1)) 
label2=np.zeros((int(7060),1))


labels=np.append(label1,label2)
shu=data
X,y=get_shuffle(shu,labels)

features = torch.FloatTensor(X)
print(features.shape[0])
y_tensor = torch.from_numpy(y)
labels = torch.squeeze(y_tensor)



g = dgl.knn_graph(features, 5, algorithm='bruteforce-blas', dist='cosine')
g = dgl.remove_self_loop(g)
g = dgl.add_self_loop(g)
adj = g.adjacency_matrix().to_dense()

adjacency_matrix_sparse = sp.csr_matrix(adj)
nnz = adjacency_matrix_sparse.getnnz()


num_rows, num_cols = adjacency_matrix_sparse.shape


adj_matrix_tensor = torch.tensor(adjacency_matrix_sparse.toarray()).long()


nonzero_coords = adj_matrix_tensor.nonzero()


nnz = nonzero_coords.size(0)


A = [(nonzero_coords.t(), torch.ones(nnz))]  # 假设权重都是1



labels_tensor = torch.tensor(labels)

# 定义十倍交叉验证
skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
ytest=np.ones((1,2))*0.5
yscore=np.ones((1,2))*0.5
probas_cnn=[]
tprs_cnn = []
sepscore_cnn = []
# 打印模型的结构
print(FastGTNs)
for fold, (train_index, test_index) in enumerate(skf.split(features, labels)):
    X_train, X_test = features[train_index], features[test_index]
    print(X_train.shape)
    y_train, y_test = labels_tensor[train_index].long(), labels_tensor[test_index].long()
    # A_train, A_test = A[train_index][:, train_index], A[test_index][:, train_index]

    # 创建 GTN 模型实例
    # model = GTN(num_edge=len(A), num_channels=2, w_in=100, w_out=64, num_class=2, num_nodes=14189, num_layers=2)  # 根据实际情况设置参数
    model = FastGTNs(num_edge_type=len(A),
                            w_in = 2560,
                            num_class=2,
                            num_nodes = 14189,
                            args=args)
    print(model)

    optimizer=torch.optim.Adam(model.parameters(),lr=0.01,weight_decay=1e-4)
    loss = nn.CrossEntropyLoss()

    num_epochs = 180  # 根据需p要设置训练轮数
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        # loss, _, _ = model(A, features, train_index, y_train, eval=False)
        loss,_,_=model(A, features, train_index, y_train, epoch=epoch)
        loss.backward()
        optimizer.step()
        print(f"Epoch {epoch+1}, Loss: {loss.item()}")
        # 在测试集上进行模型评估
    with torch.no_grad():
        # test_loss, y_pred,W = model(A, features, test_index, y_test)  # 这里可能需要根据模型的返回值进行处理
        test_loss, y_pred,W = model.forward(A, features, test_index, y_test, epoch=epoch)
        probas=y_pred
        # Assuming `probas` is your PyTorch tensor
        probas_detached = probas.detach().numpy()
        y_class = categorical_probas_to_classes(probas_detached)
        # y_class= utils.categorical_probas_to_classes(probas)
        y_test2=to_categorical(y_test)#generate the test
        print(y_test2.shape)
        print(ytest.shape)
        ytest=np.vstack((ytest,y_test2))
        y_test_tmp=y_test 
        # yscore=np.vstack((yscore,probas))
        yscore=np.vstack((yscore,probas.detach().numpy()))
        acc, precision,npv, sensitivity, specificity, mcc,f1 = calculate_performace(len(y_class), y_class,y_test)
        mean_fpr = np.linspace(0, 1, 100)
        fpr, tpr, thresholds = roc_curve(y_test, probas[:, 1].detach().numpy())
        tprs_cnn.append(interp(mean_fpr, fpr, tpr))
        tprs_cnn[-1][0] = 0.0
        roc_auc = auc(fpr, tpr)
        aupr = average_precision_score(y_test, probas[:, 1].detach().numpy())
        sepscore_cnn.append([acc, precision,npv, sensitivity, specificity, mcc,f1,roc_auc,aupr])
        print('NB:acc=%f,precision=%f,npv=%f,sensitivity=%f,specificity=%f,mcc=%f,f1=%f,roc_auc=%f,aupr=%f'
              % (acc, precision,npv, sensitivity, specificity, mcc,f1, roc_auc,aupr)  

scores=np.array(sepscore_cnn)
print("acc=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[0]*100,np.std(scores, axis=0)[0]*100))
print("precision=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[1]*100,np.std(scores, axis=0)[1]*100))
print("npv=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[2]*100,np.std(scores, axis=0)[2]*100))
print("sensitivity=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[3]*100,np.std(scores, axis=0)[3]*100))
print("specificity=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[4]*100,np.std(scores, axis=0)[4]*100))
print("mcc=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[5]*100,np.std(scores, axis=0)[5]*100))
print("f1=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[6]*100,np.std(scores, axis=0)[6]*100))
print("roc_auc=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[7]*100,np.std(scores, axis=0)[7]*100))
print("aupr=%.2f%% (+/- %.2f%%)" % (np.mean(scores, axis=0)[8]*100,np.std(scores, axis=0)[8]*100))
row=ytest.shape[0]
ytest=ytest[np.array(range(1,row)),:]
ytest_sum = pd.DataFrame(data=ytest)
ytest_sum.to_csv('')
yscore_=yscore[np.array(range(1,row)),:]
yscore_sum = pd.DataFrame(data=yscore_)
yscore_sum.to_csv('')

scores=np.array(sepscore_cnn)
result1=np.mean(scores,axis=0)
H1=result1.tolist()
sepscore_cnn.append(H1)
result=sepscore_cnn
data_csv = pd.DataFrame(data=result)
data_csv.to_csv('')
time_end = time.time()  # 记录结束时间
time_sum = time_end - time_start  # 计算的时间差为程序的执行时间，单位为秒/s
print(time_sum)
# print(ytest[:,0].shape)
# print(yscore[1:,0].shape)
fpr, tpr, _ = roc_curve(ytest[:,0], yscore[1:,0])
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
plt.savefig(r'Curve_pr_auc1.png',format='png',dpi=600)
plt.show()
