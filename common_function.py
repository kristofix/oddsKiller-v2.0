from config import max_time, threshold
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, f1_score
import numpy as np
import xgboost as xgb
from models.xgb_with_bayes_search import xgb_model
from models.neural_network import nn_model
from config import min_time, minbetodd, maxbetodd, insufficient
import pandas as pd

def removeDotFromColumnNames(df):
    df.columns = df.columns.str.replace('.', '', regex=False)
    return df

def dropMinutes(df):
    df = df[(df['framestime'] > min_time) & (df['framestime'] < max_time)]
    return df

def sortByDate(df):
    df['datetimestamp'] = pd.to_datetime(df['datetimestamp'], unit='ms')
    df = df.sort_values(by='datetimestamp')
    return df

def dropNotDraw(df):
  #drop mathces without draw in betting frame
  df['draw'] = df['frameshomescore'] - df['framesawayscore']
  df = df[df['draw'] == 0]
  return df

def oddsFilter(df):
  df = df[(df['frameshomeodd'] >= minbetodd) & (df['frameshomeodd'] <= maxbetodd) & (df['framesawayodd'] >= minbetodd) & (df['framesawayodd'] <= maxbetodd)]
  return df

def addSumStats(df):
    # Compute new columns and hold them temporarily
    sumAstats = df['frameshomeshotsOnTarget'] + df['frameshomeshotsOffTarget'] + df['frameshomeattacks'] + df['frameshomedangerousAttacks']
    sumBstats = df['framesawayshotsOnTarget'] + df['framesawayshotsOffTarget'] + df['framesawayattacks'] + df['framesawaydangerousAttacks']
    # Insert new columns before the last column
    df.insert(loc=len(df.columns) - 1, column='sumAstats', value=sumAstats)
    df.insert(loc=len(df.columns) - 1, column='sumBstats', value=sumBstats)
    return df

def dropInsufficient(df):
  df = df[(df['sumAstats'] >= insufficient) | (df['sumBstats'] >= insufficient)]
  return df

def dif_threshold(df):
  # Calculate the difference between the values in columns 'sumAstats' and 'sumBstats'
  df['diff'] = abs(df['sumAstats'] - df['sumBstats'])
  df = df[df['diff'] >= threshold]
  return df

def dropUnnecessary(df):
    cols_to_drop = ['framestime', 'frameshomescore', 'framesawayscore', 'draw', 'diff', 'datetimestamp', 'sumAstats', 'sumBstats']
    df.drop(columns=[col for col in cols_to_drop if col in df.columns], inplace=True)
    return df

def calculate_metrics(y_test, y_pred):
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    cm = confusion_matrix(y_test, y_pred)
    print(f"Test set accuracy: {accuracy}")
    print(f"Test set precision: {precision}")
    print(f"Test set recall: {recall}")
    print(f"Test set F1 Score: {f1}")
    return accuracy, precision, recall, f1

def sport_metrics(cm):
    yield1 = int((cm[1][1] + cm[2][2] - cm[0][1] - cm[0][2] - cm[1][2] - cm[2][1])) / int(
        (cm[1][1] + cm[2][2] + cm[0][1] + cm[0][2] + cm[1][2] + cm[2][1]))
    total_bets = cm[1][1] + cm[2][2] + cm[0][1] + cm[0][2] + cm[1][2] + cm[2][1]
    income = cm[1][1] + cm[2][2] - cm[0][1] - cm[0][2] - cm[1][2] - cm[2][1]
    print('Test income: ', income)
    print('Test total placed bet: ', total_bets)
    print('Test yield: ', yield1)
    return yield1, total_bets, income

def select_and_train_model(model_selector, X_train, X_test, y_train, y_test):
    if model_selector == "nn":
        nn_model(X_train, X_test, y_train, y_test)
        from tensorflow.keras.models import load_model
        loaded_model = load_model('nn_model.keras')
        y_pred = np.argmax(loaded_model.predict(X_test), axis=-1)
    elif model_selector == "xgb":
        xgb_model(X_train, X_test, y_train, y_test)
        loaded_model = xgb.XGBClassifier()
        loaded_model.load_model("best_xgb_model.model")
        y_pred = loaded_model.predict(X_test)
    return y_pred