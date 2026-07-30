from features.feature_engineering import get_final_ml_data, split_by_position, get_df_field, get_df_gk
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, cross_val_score
import numpy as np
import joblib 
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent


def prepare_traindata(df):
    df = df.drop_duplicates().sort_values(by=["season", "matchday"]).fillna(0)
    x = df.drop(columns=["target_points", "season"])
    y = df["target_points"]

    return x,y

def print_feature_importances(model, feature_names, position_name, top_n=10):
    importances = model.feature_importances_
    
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'importance': importances
    })
    
    # Absteigend sortieren
    importance_df = importance_df.sort_values(by="importance", ascending=False)
    
    print(f"\nTop {top_n} Features für {position_name}:")
    print(importance_df.head(top_n))


if __name__ == "__main__":

    RUN_GRID_SEARCH = False # für grid_search einfach auf true ändern, aktuell werden jedoch bereits diese Parameter genutzt
    TRAIN_GOALKEEPER = True
    SAFE_MODELL = False

    n_estimators = 500
    learning_rate = 0.01
    max_depth = 5
    subsample = 0.8

    df_field = get_df_field()
    df_gk = get_df_gk()
    df_field = get_final_ml_data(df_field)
    df_gk = get_final_ml_data(df_gk)

    df_def, df_mid, df_off = split_by_position(df_field)

    positions_data = {
        "Abwehr": df_def,
        "Mittelfeld": df_mid,
        "Angriff": df_off
    }

    for position_name, df in positions_data.items():
        print(f"\nStarte Training für: {position_name}")

        x, y = prepare_traindata(df)

        if not RUN_GRID_SEARCH:
                model = XGBRegressor(
                    n_estimators=n_estimators,
                    learning_rate=learning_rate,
                    max_depth=max_depth,
                    subsample=subsample,
                    random_state=42,
                    n_jobs=1
                )
                
                scores = cross_val_score(model, x, y, cv=TimeSeriesSplit(n_splits=5), scoring="neg_mean_absolute_error")
                mae = scores.mean() * -1  
                print(f"Bester CV MAE für {position_name}: {mae:.2f}")

                model.fit(x, y)
                if SAFE_MODELL:
                    filename = MODEL_DIR / f"model_{position_name}.pkl"
                    joblib.dump(model, filename)
                    print(f"Model für {position_name} gespeichert")

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
                cv=TimeSeriesSplit(n_splits=5),
                scoring={"MAE": "neg_mean_absolute_error", "RMSE": "neg_root_mean_squared_error"},
                refit="MAE",
                verbose=1,
                n_jobs=1
            )

            grid_search.fit(x, y)

            best_model = grid_search.best_estimator_

            best_idx = grid_search.best_index_
            
            best_mae = grid_search.cv_results_['mean_test_MAE'][best_idx] * -1
            best_rmse = grid_search.cv_results_['mean_test_RMSE'][best_idx] * -1

            importances = best_model.feature_importances_
            feature_names = x.columns

            print_feature_importances(best_model, x.columns, position_name, top_n=10)
            print(f"Beste Parameter: {grid_search.best_params_}")
            print(f"Bester CV MAE: {best_mae:.2f}")
            print(f"Bester CV RMSE: {best_rmse:.2f}")

            if SAFE_MODELL:
                filename = MODEL_DIR / f"model_{position_name}_best.pkl"
                joblib.dump(best_model, filename)
                print(f"Bestes Model für {position_name} gespeichert")

    # goalkeeper
    if TRAIN_GOALKEEPER:
        print(f"\nStarte Training für: Torwart")

        x_gk, y_gk = prepare_traindata(df_gk)

        model_gk = XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=subsample,
            random_state=42,
            n_jobs=1
        )

        scores = cross_val_score(model_gk, x_gk, y_gk, cv=TimeSeriesSplit(n_splits=5), scoring="neg_mean_absolute_error")

        model_gk.fit(x_gk, y_gk)

        mae_gk = scores.mean() * -1          

        print(f"MAE Torwart: {mae_gk:.2f}")

        if SAFE_MODELL:
            joblib.dump(model_gk, MODEL_DIR / "model_gk.pkl")
            print("Model GK gespeichert")

    