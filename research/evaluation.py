"""Metrics that never count abstentions as successful decisions."""
import numpy as np
from scipy.special import expit
from sklearn.metrics import confusion_matrix,precision_recall_fscore_support,accuracy_score,f1_score,brier_score_loss
from schema import LABELS

def calibration_error(y,p,bins=10):
    total=0.;details=[]
    for low,high in zip(np.linspace(0,1,bins+1)[:-1],np.linspace(0,1,bins+1)[1:]):
        mask=(p>=low)&(p<high if high<1 else p<=high)
        if mask.any():
            accuracy=float(y[mask].mean());score=float(p[mask].mean());count=int(mask.sum())
            total+=count/len(y)*abs(accuracy-score);details.append({'lower':float(low),'upper':float(high),'n':count,'positive_rate':accuracy,'mean_probability':score})
    return {'ece':total,'bins':details}

def metrics(labels,logits,temperature=1.,thresholds=None):
    labels=np.asarray(labels);logits=np.asarray(logits);p=expit(logits[:,0]/temperature);y=labels[:,0].astype(int)
    pred=p>=.5;tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    precision,recall,f1,_=precision_recall_fscore_support(y,pred,average='binary',zero_division=0)
    result={'n':len(y),'binary':{'precision':float(precision),'recall':float(recall),'f1':float(f1),'accuracy':float(accuracy_score(y,pred)),
      'confusion':{'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp)},'false_positive_rate':float(fp/max(1,fp+tn)),'false_negative_rate':float(fn/max(1,fn+tp))},
      'calibration':{'brier':float(brier_score_loss(y,p)),**calibration_error(y,p)},'categories':{}}
    supported=[]
    for i,label in enumerate(LABELS):
        known=labels[:,i+1]>=0;target=labels[known,i+1];prediction=logits[known,i+1]>=0
        pr,re,f,_=precision_recall_fscore_support(target,prediction,average='binary',zero_division=0)
        result['categories'][label]={'known':int(known.sum()),'positive':int(target.sum()),'precision':float(pr),'recall':float(re),'f1':float(f)}
        if target.sum():supported.append(float(f))
    result['macro_f1_supported_categories']=float(np.mean(supported)) if supported else None
    if thresholds:
        accepted_high=p>=thresholds['altered'];accepted_low=p<=thresholds['preserved'];accepted=accepted_high|accepted_low
        decisions=accepted_high.astype(int);correct=(decisions==y)&accepted
        result['selective']={'coverage':float(accepted.mean()),'abstained':int((~accepted).sum()),
            'selective_accuracy':float(correct.sum()/accepted.sum()) if accepted.any() else None,
            'resolved_correct_fraction':float(correct.mean()),'thresholds':thresholds,
            'preserved_decisions':int(accepted_low.sum()),'altered_decisions':int(accepted_high.sum())}
    return result

def bootstrap(rows,labels,logits,samples=1000):
    groups={}
    for i,r in enumerate(rows):groups.setdefault(r['group'],[]).append(i)
    keys=list(groups);rng=np.random.default_rng(1729);scores=[]
    for _ in range(samples):
        indices=np.concatenate([groups[k] for k in rng.choice(keys,len(keys),replace=True)])
        scores.append(f1_score(labels[indices,0],logits[indices,0]>0,zero_division=0))
    return {'unit':'source/document group','groups':len(keys),'resamples':samples,'binary_f1_95_percentile_ci':np.quantile(scores,[.025,.975]).tolist()}
