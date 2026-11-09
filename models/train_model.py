from features.feature_engineering import get_final_ml_data, split_by_position, get_df_field, get_df_gk
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, RandomizedSearchCV, cross_val_score
import numpy as np
import joblib 
from pathlib import Path
import time 
import datetime
import os

# run with: python -m models.train_model


MODEL_DIR = Path(__file__).resolve().parent

start_time = time.perf_counter()

def prepare_traindata(df):
    df = df.drop_duplicates().sort_values(by=["season", "matchday"])
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

    RUN_GRID_SEARCH = True # = RandomizedSearchCV
    TRAIN_GOALKEEPER = True
    SAFE_MODELL = True 

    model_results = []

    n_estimators = 500
    learning_rate = 0.01
    max_depth = 5
    subsample = 0.8
    n_iter = 100

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
    if TRAIN_GOALKEEPER: # wenn man möchte, kann df_gk direkt in position_data gepackt werden und der if-Block gelöscht werden
        positions_data["Torwart"] = df_gk

    for position_name, df in positions_data.items():
        print(f"\n{'-'*40}\nStarte Training für: {position_name}\n{'-'*40}")

        x, y = prepare_traindata(df)

        if RUN_GRID_SEARCH:
            param_grid = {
                'n_estimators': [100, 300, 500, 700, 1000],
                'learning_rate': [0.01, 0.03, 0.05],
                'max_depth': [2, 3, 4, 5],
                'subsample': [0.6, 0.7, 0.8, 0.9],
                'min_child_weight': [1, 5, 10, 20],
                'colsample_bytree': [0.5, 0.7, 0.9],
            }

            xgb = XGBRegressor(random_state=42, n_jobs=-1) 
            grid_search = RandomizedSearchCV( # ursprünglich GridSearchCV, aber RandomizedSearchCV ist schneller und liefert oft ähnliche Ergebnisse
                estimator=xgb,
                param_distributions=param_grid, # bei GridSearchCV: param_grid=param_grid,
                cv=TimeSeriesSplit(n_splits=5),
                scoring={"MAE": "neg_mean_absolute_error", "RMSE": "neg_root_mean_squared_error"},
                refit="MAE",
                verbose=1,
                n_jobs=1,
                n_iter=n_iter, # Anzahl der zufälligen Kombinationen, die getestet werden sollen
                random_state=42
            )
            grid_search.fit(x, y)

            final_model = grid_search.best_estimator_
            best_idx = grid_search.best_index_
            final_mae = grid_search.cv_results_['mean_test_MAE'][best_idx] * -1
            final_rmse = grid_search.cv_results_['mean_test_RMSE'][best_idx] * -1
            final_params = grid_search.best_params_

        else: 
            final_model = XGBRegressor(
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                max_depth=max_depth,
                subsample=subsample,
                random_state=42,
                n_jobs=-1,
            )
            
            scores = cross_val_score(final_model, x, y, cv=TimeSeriesSplit(n_splits=5), scoring="neg_mean_absolute_error")
            final_mae = scores.mean() * -1  
            final_rmse = 0.0 # Platzhalter
            final_params = {
                "n_estimators": n_estimators,
                "learning_rate": learning_rate,
                "max_depth": max_depth,
                "subsample": subsample
            }
            final_model.fit(x, y)


        print(f"Beste Parameter: {final_params}")
        print(f"Bester CV MAE: {final_mae:.2f}")
        if RUN_GRID_SEARCH:
            print(f"Bester CV RMSE: {final_rmse:.2f}")

        print_feature_importances(final_model, x.columns, position_name, top_n=10)

        importances = final_model.feature_importances_
        imp_df = pd.DataFrame({'Feature': x.columns, 'importance': importances}).sort_values(by="importance", ascending=False)
        top_3_str = ", ".join(imp_df["Feature"].head(3).tolist())

        model_results.append({
            "position": position_name,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Grid_Search": RUN_GRID_SEARCH,
            "n_iter": n_iter if RUN_GRID_SEARCH else None,
            "best_mae": final_mae,
            "best_rmse": final_rmse,
            "n_estimators": final_params["n_estimators"],
            "learning_rate": final_params["learning_rate"],
            "max_depth": final_params["max_depth"],
            "subsample": final_params["subsample"],
            "min_child_weight": final_params.get("min_child_weight", 1),
            "colsample_bytree": final_params.get("colsample_bytree", 1.0),
            "top_features": top_3_str
        })

        if SAFE_MODELL:
            suffix = "_best" if RUN_GRID_SEARCH else ""
            filename = MODEL_DIR / f"model_{position_name.lower()}{suffix}.pkl"
            joblib.dump(final_model, filename)
            print(f"Model für {position_name} gespeichert unter {filename.name}")

    if model_results:
        df_results = pd.DataFrame(model_results)
        results_path = MODEL_DIR / "model_results.csv"

        if results_path.is_file():
            df_old = pd.read_csv(results_path)
            # Alte Läufe haben diese Parameter nicht getunt, also galten die XGBoost-Defaults
            for col, default in {"min_child_weight": 1, "colsample_bytree": 1.0}.items():
                if col not in df_old.columns:
                    df_old[col] = default
            df_results = pd.concat([df_old, df_results], ignore_index=True)[df_results.columns]

        df_results.to_csv(results_path, index=False)
        print(f"\nMetrics erfolgreich in {results_path.name} gespeichert.")

    end_time = time.perf_counter()
    print(f"Dauer: {(end_time - start_time) / 60:.2f} Minuten")
