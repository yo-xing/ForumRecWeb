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

    client = boto3.client('s3')#, aws_access_key_id=aws_id, aws_secret_access_key=aws_secret)
    csv_obj = client.get_object(Bucket=bucket_name, Key=samplecsv_key)['Body'].read().decode('utf-8')
    new = pd.read_csv(StringIO(csv_obj))

    s3 = S3FileSystem()
    user_indicies_key = 'user_indicies.npy'
    post_indicies_key = 'post_indicies.npy'

    user_indicies = np.load(s3.open('{}/{}'.format(bucket_name, user_indicies_key)))
    post_indicies = np.load(s3.open('{}/{}'.format(bucket_name, post_indicies_key)))

    model_client = client.get_object(Bucket=bucket_name, Key=pickle_key)['Body'].read()
    model = pickle.loads(model_client)

    item_features_npz = client.get_object(Bucket=bucket_name, Key=item_features_key)['Body'].read()
    # user_indicies = np.load('user_indicies.npy')
    # print(max(user_indicies))
    # post_indicies = np.load('post_indicies.npy')
    # print(max(post_indicies))
    # model = pickle.load(open("savefile.pickle", "rb"))
    dataset = Dataset()
    dataset.fit((x for x in user_indicies),
            (x for x in post_indicies))
    dummies = range(max(user_indicies) + 1, max(user_indicies)+100)
    dataset.fit_partial((x for x in dummies))
    print(dataset.interactions_shape())
    # new = pd.read_csv(f)
    print(new.columns)
    new = new[['Score', 'Body', 'OwnerUserId', 'ParentId', 'Id', 'user_indicies',
       'post_indicies']]
    print(new.columns)
    print(new[['Score','OwnerUserId', 'ParentId', 'Id', 'user_indicies',
       'post_indicies']].values[0])
    new_user_indicies = dict()
    for i in range(len(new.OwnerUserId.unique())):
        new_user_indicies[new.OwnerUserId.unique()[i]] = dummies[i]
    new['user_indicies'] = new.OwnerUserId.apply(lambda x: new_user_indicies[x])
    print(new['user_indicies'].values)
    dataset.fit_partial((x for x in new.user_indicies.values),
             (x for x in new.post_indicies.values))
    (new_interactions, new_weights) = dataset.build_interactions(((x[5], x[6], x[0]) for x in new.values))
    #interactions = sparse.load_npz("interactions.npz")
    # item_features = sparse.load_npz("item_features.npz")
    item_features = sparse.load_npz(item_features_npz)
    for i in new.user_indicies.unique():
          print(i, 'mean user embedding before refitting :', np.mean(model.user_embeddings[i]))
    print(new_interactions.shape)
    model = model.fit_partial(new_interactions, item_features = item_features, sample_weight = new_weights,
         epochs=10, num_threads=8, verbose=True)
    for i in new.user_indicies.unique():
          print(i, 'mean user embedding after refitting:', np.mean(model.user_embeddings[i]))

    # with open('savefile.pickle', 'wb') as fle:
    #     pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL)

    s3_resource = boto3.resource('s3')
    s3_resource.Object(bucket, pickle_key).put(Body=pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL))

        #item_dict ={}
#     df = filtered_q.sort_values('post_indicies').reset_index()
#     for i in range(df.shape[0]):
#         item_dict[(df.loc[i,'post_indicies'])] = df.loc[i,'Id']
#     mean_recommendation_user(model, interactions,  item_features, 3,
#                                item_dict, threshold = 0,nrec_items = 50, show = True)



if __name__ == "__main__":
    main()
