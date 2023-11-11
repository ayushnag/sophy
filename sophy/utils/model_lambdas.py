import numpy as np
import pandas as pd
import re

def project(lambdas, newdata, return_lfx=False, mask=None, quiet=False):
    
  meta = lambdas[1:]
  lambdas = lambdas[0]
  
  is_cat = lambdas[lambdas["type"] == "categorical", "feature"].unique()
  nms = np.unique(np.concatenate([lambdas["var"][lambdas["lambda"] != 0].str.split(", ").explode()]))
  clamp_limits = lambdas[lambdas["type"] == "linear", ["feature", "min", "max"]]
  lambdas = lambdas[lambdas["lambda"] != 0]
  lambdas = lambdas.groupby(lambdas["type"].ne("hinge").cumsum()).apply(lambda x: x.drop("type", axis=1))
  
  missing_vars = set(nms) - set(newdata.columns)
  if len(missing_vars) > 0:
      raise ValueError("Variables missing in newdata: " + ", ".join(missing_vars))
  
  newdata = newdata[nms]
  na = newdata.isnull().any(axis=1)
  newdata = newdata.dropna()
    
  def clamp_features(row):
      x = row[feature]
      clamp_max = clamp_limits[clamp_limits["feature"] == feature]["max"]
      clamp_min = clamp_limits[clamp_limits["feature"] == feature]["min"]
      row[feature] = max(min(x, clamp_max), clamp_min)
      return row

  for feature in set(nms) - set(is_cat):
      newdata = newdata.apply(clamp_features, axis=1)

  k_hinge = len(lambdas[lambdas["type"] == "hinge"])
  k_other = len(lambdas[lambdas["type"] != "hinge"])

  def categorical_features(row):
    for feature in is_cat:
        levels = lambdas[lambdas["feature"] == feature, "level"].unique()
        for level in levels:
            row[feature + "_" + level] = (row[feature] == level)
    return row

  newdata = newdata.apply(categorical_features, axis=1)

  pred_lin = np.zeros((newdata.shape[0], k_other))
  pred_quad = np.zeros((newdata.shape[0], k_other))
  pred_cub = np.zeros((newdata.shape[0], k_other))
  pred_hinge = np.zeros((newdata.shape[0], k_hinge))

  for i, lambda_row in enumerate(lambdas.itertuples(index=False)):
      feature = lambda_row.feature
      var = lambda_row.var
      typ = lambda_row.type
      if typ == "linear":
          pred_lin[:, i] = lambda_row.lambda * newdata[var]
      elif typ == "quadratic":
          pred_quad[:, i] = lambda_row.lambda * newdata[var] ** 2
      elif typ == "cubic":
          pred_cub[:, i] = lambda_row.lambda * newdata[var] ** 3
      elif typ == "hinge":
          level = lambda_row.level
          pred_hinge[:, i] = lambda_row.lambda * (newdata[var] >= level)

  lin_pred = np.sum(pred_lin, axis=1)
  quad_pred = np.sum(pred_quad, axis=1)
  cub_pred = np.sum(pred_cub, axis=1)
  hinge_pred = np.sum(pred_hinge, axis=1)

  pred = np.exp(lin_pred + quad_pred + cub_pred + hinge_pred)

  if return_lfx:
      pred_lfx = np.exp(lin_pred + quad_pred + cub_pred + hinge_pred)

  if mask is not None:
      pred_raw = 0
      pred_logistic = 0
      pred_cloglog = 0
      pred_raw[~na] = pred
      pred_logistic[~na] = 1 / (1 + np.exp(-pred))
      pred_cloglog[~na] = 1 - np.exp(-np.exp(pred))

  if not quiet:
      print("Done.")

  if return_lfx:
      return pred_raw, pred_logistic, pred_cloglog, pred_lfx
  else:
      return pred_raw, pred_logistic, pred_cloglog
  

def parse_lambdas(lambdas_file: str) -> tuple[pd.DataFrame, dict]:
  # open file and read lines
  with open(lambdas_file, 'r') as file:
    lambdas: list = file.readlines()

  parsed: list = []
  meta: dict = {}
  prefix_to_type: dict = {'==': 'categorical', '<=': 'threshold', '^': 'quadratic', '*': 'product', '`': 'reverse_hinge', "'": 'forward_hinge'}
  for line in lambdas:
    # split the line into parts
    parts: list = re.split(', ', line)
    # if there are 4 parts, it's a feature line
    if len(parts) == 4:
      feature, _lambda, min, max = parts
      feature: str = feature.replace('=', '==').replace('<', '<=')
      # extract the prefix from the feature
      prefix: str = re.sub("\\w|\\.|-|\\(|\\)", "", feature)
      # replace prefix with feature type (no prefix means its linear)
      typ: str = prefix_to_type[prefix] if prefix in prefix_to_type else 'linear'
      # remove the prefix from the feature
      feature: str = re.sub('\\^2|\\(.*?<=|\\((.*?)==.*?|`|\\\'|\\)', "\\1", feature)
      parsed.append([feature, typ, float(_lambda), float(min), float(max)])
    elif len(parts) == 2:
      # if there are 2 parts, it's a metadata line
      key, value = parts
      meta[key] = float(value)

  parsed_df = pd.DataFrame(parsed, columns=['feature', 'type', 'lambda', 'min', 'max'])
  parsed_df['type'] = pd.Categorical(parsed_df['type'])
  # return the parsed dataframe and the metadata
  return parsed_df, meta



