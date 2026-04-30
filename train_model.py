from feature_engineering import get_final_ml_data
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV
import numpy as np



def split_df(df, test_size = 0.2): # 0.2 = 80% Training, 20% Test split

    timeline = df[['season', 'matchday']].drop_duplicates().sort_values(by=['season', 'matchday'])

    split_index = int(len(timeline) * (1-test_size))

    if split_index == len(timeline): # Edge Case aktuell ganz am Anfang der Saison
        split_index = len(timeline) - 1

    train_timeline = timeline.iloc[:split_index]
    test_timeline = timeline.iloc[split_index:]

    train_data = pd.merge(df, train_timeline, on=['season', 'matchday'], how='inner')
    test_data = pd.merge(df, test_timeline, on=['season', 'matchday'], how='inner')

    train_data = train_data.fillna(0)
    test_data = test_data.fillna(0)

    X_train = train_data.drop(columns=["target_points", "season"])
    y_train = train_data["target_points"]
    X_test = test_data.drop(columns=["target_points", "season"])
    y_test = test_data["target_points"]
    
    print(f"Trainings-Spiele: {len(X_train)} | Test-Spiele: {len(X_test)}") # für debugging 
    
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":

    df_field, df_gk = get_final_ml_data()

    X_train_field, X_test_field, y_train_field,  y_test_field = split_df(df_field)

    X_train_gk, X_test_gk, y_train_gk, y_test_gk = split_df(df_gk)

    RUN_GRID_SEARCH = False  # für grid_search einfach auf true ändern, aktuell werden jedoch bereits diese Parameter genutzt

    n_estimators = 500
    learning_rate = 0.01
    max_depth = 5
    subsample = 0.8

    # field_players
    model_field = XGBRegressor(
        n_estimators = n_estimators,
        learning_rate = learning_rate,
        max_depth = max_depth, 
        subsample=subsample, 
        random_state=42,
        n_jobs=1 
    )

    model_field.fit(X_train_field, y_train_field)

    model_field_pred = model_field.predict(X_test_field)

    mae_field = mean_absolute_error(y_test_field, model_field_pred)

    rmse_field = np.sqrt(mean_squared_error(y_test_field, model_field_pred))

    # goalkeeper
    model_gk = XGBRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        subsample=subsample,
        random_state=42,
        n_jobs=1
    )

    model_gk.fit(X_train_gk, y_train_gk)

    model_gk_pred = model_gk.predict(X_test_gk)

    mae_gk = mean_absolute_error(y_test_gk, model_gk_pred)

    rmse_gk = np.sqrt(mean_squared_error(y_test_gk, model_gk_pred))



    print(f"Parameter: {n_estimators}, {learning_rate}, {max_depth}, {subsample}, 42")
    print(f"mae_field: {mae_field:.2f}")
    print(f"rmse_field: {rmse_field:.2f}")

    print(f"mae_gk: {mae_gk:.2f}")
    print(f"rmse_gk: {rmse_gk:.2f}") 


    if RUN_GRID_SEARCH:

        param_grid = {
            'n_estimators': [100, 300, 500],
            'learning_rate': [0.01, 0.05, 0.1],
            'max_depth': [3, 5, 7],
            'subsample': [0.8, 1.0] 
        }

        xgb = XGBRegressor(random_state=42)
        grid_search = GridSearchCV(
            estimator= xgb,
            param_grid=param_grid,
            cv=5,
            scoring="neg_mean_absolute_error",
            verbose=2,
            n_jobs=1
        )

        grid_search.fit(X_train_field, y_train_field)

        print(f"Besten Parameter: {grid_search.best_params_}")
        print(f"Bester Score (neg MAE): {grid_search.best_score_:.2f}")

        best_model = grid_search.best_estimator_
        best_pred = best_model.predict(X_test_field)
        best_mae = mean_absolute_error(y_test_field, best_pred)

        print(f"MAE best_modell auf Testdaten: {best_mae:.2f}")
        # Besten Parameter: 
        # {'learning_rate': 0.01, 'max_depth': 5, 'n_estimators': 500, 'subsample': 0.8}
        # Bester Score (neg MAE): -50.51
        # MAE best_modell auf Testdaten: 45.86