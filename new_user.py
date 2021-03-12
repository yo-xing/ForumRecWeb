from lightfm import LightFM
import pandas as pd
import numpy as np
import os
from scipy.sparse import csr_matrix
from lightfm.cross_validation import random_train_test_split
from lightfm.evaluation import auc_score, precision_at_k, recall_at_k, reciprocal_rank
from lightfm import LightFM
import re
import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy import sparse
import pickle
import json
import sys
from lightfm.data import Dataset

import boto3
from s3fs.core import S3FileSystem
from io import StringIO


def main():
#     n = len(sys.argv)
#     if n > 0:
#         f = sys.argv[0]
#     else:
#         f = 'new_sample.csv'

    # Start imports from s3
    bucket_name = 'forumrecbucket'
    samplecsv_key = 'new_sample.csv'
    pickle_key = 'savefile.pickle'
    item_features_key = 'item_features.npz'
    post_mappings_key = 'post_mappings.csv'

    client = boto3.client('s3')#, aws_access_key_id=aws_id, aws_secret_access_key=aws_secret)
    csv_obj = client.get_object(Bucket=bucket_name, Key=samplecsv_key)['Body'].read().decode('utf-8')
    new = pd.read_csv(StringIO(csv_obj))

    s3 = S3FileSystem()
    user_indicies_key = 'user_indicies.npy'
    post_indicies_key = 'post_indicies.npy'

    user_indicies = np.load(s3.open('{}/{}'.format(bucket_name, user_indicies_key)))
    post_indicies = np.load(s3.open('{}/{}'.format(bucket_name, post_indicies_key)))
    post_mappings_obj = client.get_object(Bucket=bucket_name, Key=post_mappings_key)['Body'].read().decode('utf-8')
    post_mappings = pd.read_csv(StringIO(post_mappings_obj))

    post_mappings.columns = ['ParentId', 'post_indicies']
    post_mappings.index = post_mappings['ParentId']
    post_mappings = post_mappings['post_indicies']
    post_ind = lambda x: post_mappings.loc[x]

    model_client = client.get_object(Bucket=bucket_name, Key=pickle_key)['Body'].read()
    model = pickle.loads(model_client)
    print('user_indicies length:  ', len(user_indicies))
    print('post_indicies length:  ', len(post_indicies))
    # item_features_npz = client.get_object(Bucket=bucket_name, Key=item_features_key)['Body'].read()
    # item_features_npz = csr_matrix(item_features_npz)
    # user_indicies = np.load('user_indicies.npy')
    # print(max(user_indicies))
    # post_indicies = np.load('post_indicies.npy')
    # print(max(post_indicies))
    # model = pickle.load(open("savefile.pickle", "rb"))
    dataset = Dataset()
    dataset.fit((x for x in user_indicies),
            (x for x in post_indicies))
    dummies = range(max(user_indicies) + 1, 876)
    dataset.fit_partial((x for x in dummies))
    print(dataset.interactions_shape())
    # new = pd.read_csv(f)
    new['post_indicies'] = new['ParentId'].apply(post_ind)
    new_user_indicies = dict()
    for i in range(len(new.OwnerUserId.unique())):
        new_user_indicies[new.OwnerUserId.unique()[i]] = dummies[i]
    new['user_indicies'] = new.OwnerUserId.apply(lambda x: new_user_indicies[x])
    print(new['user_indicies'].values)
    new_user_indicies = dict()
    for i in range(len(new.OwnerUserId.unique())):
        new_user_indicies[new.OwnerUserId.unique()[i]] = dummies[i]
    new['user_indicies'] = new.OwnerUserId.apply(lambda x: new_user_indicies[x])
    #user_indicies = np.append(user_indicies, new.user_indicies.unique())
    #######
    #np.save('user_indicies.npy', user_indicies)
    #######
    new = new[['user_indicies','post_indicies', 'Score', 'OwnerUserId', 'ParentId']]
    dataset.fit_partial((x for x in new.user_indicies.values),
             (x for x in new.post_indicies.values))
    (new_interactions, new_weights) = dataset.build_interactions(((x[0], x[1], x[2]) for x in new.values))
    print(new_interactions.shape)
    #interactions = sparse.load_npz("interactions.npz")
    item_features = sparse.load_npz("item_features.npz")
    print(item_features.shape)
    # item_features = sparse.load_npz(item_features_npz)
    for i in new.user_indicies.unique():
          print(i, 'mean user embedding before refitting :', np.mean(model.user_embeddings[i]))
    print(new_interactions.shape)
    model = model.fit_partial(new_interactions, item_features = item_features, sample_weight = new_weights,
         epochs=10,verbose=True)
    for i in new.user_indicies.unique():
          print(i, 'mean user embedding after refitting:', np.mean(model.user_embeddings[i]))
            
    nq = pd.read_csv('new_questions.csv')   
    
    
    csv_buffer = StringIO()
    s3_resource = boto3.resource('s3')
    
    for i in new.user_indicies.unique():
        scores = pd.Series(model.predict(int(i),nq.post_indicies.values, item_features=item_features))
        temp = nq.copy()
        temp['reccomendation'] = scores.values

        temp.to_csv(csv_buffer, index=False)
        s3_resource.Object(bucket_name, 'new_recs.csv').put(Body=csv_buffer.getvalue())
  
    

    # with open('savefile.pickle', 'wb') as fle:
    #     pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL)

    s3_resource.Object(bucket_name, pickle_key).put(Body=pickle.dumps(model))#, protocol=pickle.HIGHEST_PROTOCOL))


    

    # s3_resource = boto3.resource('s3')
    # s3_resource.Object(bucket_name, pickle_key).put(Body=pickle.dumps(model))#, protocol=pickle.HIGHEST_PROTOCOL))

        #item_dict ={}
#     df = filtered_q.sort_values('post_indicies').reset_index()
#     for i in range(df.shape[0]):
#         item_dict[(df.loc[i,'post_indicies'])] = df.loc[i,'Id']
#     mean_recommendation_user(model, interactions,  item_features, 3,
#                                item_dict, threshold = 0,nrec_items = 50, show = True)


    # write new user recommendations to new_recs.csv, include title, url, id


if __name__ == "__main__":
    main()
