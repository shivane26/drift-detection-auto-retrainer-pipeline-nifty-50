# Automated Drift Detection & Auto-Retraining Pipeline for NIFTY 50 (MLOps)

               +--------------------+
               |   yfinance (^NSEI) |
               +---------+----------+
                         |
                         v
                  Daily data fetch
                         |
                         v
               +---------------------+
               | feature generation  |
               +---------------------+
                         |
                         v
               +---------------------+
               | Drift detection     | <-- Evidently
               +----+----------------+
                    |      |
                No  |      | Yes (drift)
                    v      v
           Use current model   Retrain pipeline triggers
           (deployed API)      retrain.py -> new model.pkl
                    |               |
                    v               v
              FastAPI (Render)   Commit model -> GitHub -> Deploy
