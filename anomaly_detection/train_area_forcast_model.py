import math
import os
import tempfile

import pandas as pd
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
from transformers import EarlyStoppingCallback, Trainer, TrainingArguments, set_seed

from tsfm_public import (
    TimeSeriesPreprocessor,
    TinyTimeMixerForPrediction,
    TrackingCallback,
    count_parameters,
    get_datasets,
)
from tsfm_public.toolkit.visualization import plot_predictions
import argparse
import uuid


SEED = 42
set_seed(SEED)

# Results dir

# TTM model branch
# Use main for 512-96 model
# Use "1024_96_v1" for 1024-96 model
TTM_MODEL_REVISION = "1024_96_v1"

# Forecasting parameters
context_length = 1024
forecast_length = 96
fewshot_fraction = 0.05


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--curr_cluster",
        default="0",
        type=str,
        help=("current cluster to train."),
    )

    parser.add_argument(
        "--epochs",
        default=60,
        type=int,
        help=("current cluster to train."),
    )
    args = parser.parse_args()
    curr_cluster = args.curr_cluster
    epochs = args.epochs

    clusters_td = pd.read_csv(
        f"/home/mohamed/Mohamed/Vodafone_project/projects/app/visualization/govs_clusters_dir/counts_{curr_cluster}.csv"
    )
    clusters_td["time"] = pd.to_datetime(clusters_td["time"])
    data_length = len(clusters_td)
    train_len = int(data_length * 0.90)
    valid_len = int(data_length * 0.05)
    test_len = int(data_length * 0.05)
    timestamp_column = "time"
    id_columns = []
    target_columns = ["count"]
    split_config = {
        "train": 0.90,
        "test": 0.05,
    }
    data = clusters_td

    column_specifiers = {
        "timestamp_column": timestamp_column,
        "id_columns": id_columns,
        "target_columns": target_columns,
        "control_columns": [],
    }

    tsp = TimeSeriesPreprocessor(
        **column_specifiers,
        context_length=context_length,
        prediction_length=forecast_length,
        scaling=True,
        encode_categorical=False,
        scaler_type="standard",
    )

    train_dataset, valid_dataset, test_dataset = get_datasets(
        tsp,
        data,
        split_config,
        fewshot_fraction=fewshot_fraction,
        fewshot_location="first",
    )
    print(
        f"Data lengths: train = {len(train_dataset)}, val = {len(valid_dataset)}, test = {len(test_dataset)}"
    )

    fine_tune_model = TinyTimeMixerForPrediction.from_pretrained(
        "ibm-granite/granite-timeseries-ttm-v1",
        revision=TTM_MODEL_REVISION,
        head_dropout=0.7,
    )
    for param in fine_tune_model.backbone.parameters():
        param.requires_grad = False

    # Important parameters
    learning_rate = 0.001
    num_epochs = epochs  # Ideally, we need more epochs (try offline preferably in a gpu for faster computation)
    batch_size = 2048

    os.environ["WANDB_PROJECT"] = "govs_forcast_models_by_cluster"
    OUT_DIR = (
        "/home/mohamed/Mohamed/Vodafone_project/projects/app/files/forcast_models/govs"
    )

    finetune_forecast_args = TrainingArguments(
        output_dir=os.path.join(OUT_DIR, f"{curr_cluster}"),
        overwrite_output_dir=True,
        learning_rate=learning_rate,
        num_train_epochs=num_epochs,
        do_eval=True,
        eval_strategy="steps",
        eval_steps=50,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        dataloader_num_workers=8,
        save_strategy="steps",
        save_steps=50,
        logging_strategy="steps",
        logging_steps=50,
        save_total_limit=1,
        logging_dir=os.path.join(
            OUT_DIR, "logs"
        ),  # Make sure to specify a logging directory
        load_best_model_at_end=True,  # Load the best model when training ends
        metric_for_best_model="eval_loss",  # Metric to monitor for early stopping
        greater_is_better=False,  # For loss
        report_to="wandb",  # enable logging to W&B
        run_name=f"cluster_{curr_cluster}_run_{uuid.uuid4()}",  # name of the W&B run (optional)
    )

    # Create the early stopping callback
    early_stopping_callback = EarlyStoppingCallback(
        early_stopping_patience=20,  # Number of epochs with no improvement after which to stop
        early_stopping_threshold=0.0,  # Minimum improvement required to consider as improvement
    )
    tracking_callback = TrackingCallback()

    # Optimizer and scheduler
    optimizer = AdamW(fine_tune_model.parameters(), lr=learning_rate)
    scheduler = OneCycleLR(
        optimizer,
        learning_rate,
        epochs=num_epochs,
        steps_per_epoch=math.ceil(len(train_dataset) / (batch_size)),
    )

    finetune_forecast_trainer = Trainer(
        model=fine_tune_model,
        args=finetune_forecast_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        callbacks=[early_stopping_callback, tracking_callback],
        optimizers=(optimizer, scheduler),
    )

    # Fine tune
    finetune_forecast_trainer.train()


if __name__ == "__main__":
    main()
