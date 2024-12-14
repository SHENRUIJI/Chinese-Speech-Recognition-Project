import torch
import data
from models.conv import GatedConv
from tqdm import tqdm
from decoder import GreedyDecoder
import joblib
from config import TRAIN_PATH, DEV_PATH, LABEL_PATH
import os
import numpy as np
import json
import matplotlib.pyplot as plt

# Помощная функция для проверки содержимого индексного файла
# 验证索引文件内容的辅助函数
def validate_index_file(index_path):
    with open(index_path) as f:
        idx = f.readlines()
    idx = [x.strip().split(",", 1) for x in idx]
    
    invalid_entries = []
    for i, (wav, _) in enumerate(idx):
        abs_wav = os.path.abspath(wav)
        trn_file = abs_wav + ".trn"
        if not os.path.exists(abs_wav) or not os.path.exists(trn_file):
            invalid_entries.append((i, abs_wav, trn_file))
    
    if invalid_entries:
        print("Found invalid entries in the index file:")
        for i, abs_wav, trn_file in invalid_entries:
            print(f"Entry {i}: wav={abs_wav}, trn={trn_file}")
    else:
        print("All entries in the index file are valid.")


def train(
    model,
    epochs=50,
    batch_size=128,
    train_index_path=TRAIN_PATH,
    dev_index_path=DEV_PATH,
    labels_path=LABEL_PATH,
    learning_rate=0.001,
    momentum=0.8,
    max_grad_norm=0.2,
    weight_decay=0,
):
    # Проверка содержимого индексных файлов
    # 验证索引文件内容
    validate_index_file(train_index_path)
    validate_index_file(dev_index_path)

    train_dataset = data.MASRDataset(train_index_path, labels_path)
    batchs = (len(train_dataset) + batch_size - 1) // batch_size
    dev_dataset = data.MASRDataset(dev_index_path, labels_path)
    
    train_dataloader = data.MASRDataLoader(
        train_dataset, batch_size=batch_size, num_workers=0, shuffle=True
    )
    dev_dataloader = data.MASRDataLoader(
        dev_dataset, batch_size=batch_size, num_workers=0
    )
    
    parameters = model.parameters()
    optimizer = torch.optim.SGD(
        parameters,
        lr=learning_rate,
        momentum=momentum,
        nesterov=True,
        weight_decay=weight_decay,
    )
    ctcloss = torch.nn.CTCLoss(reduction='mean')  # Использование встроенного CTCLoss
                                                  # 使用内置CTCLoss
    
    lr_sched = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.985)

    best_cer = float('inf')
    best_model_path = "pretrained/best_model.pth"
    
    # Инициализация списков для записи статистики
    # 初始化记录列表
    epoch_losses = []
    epoch_cers = []
    learning_rates = []

    for epoch in range(epochs):
        epoch_loss = 0
        lr_sched.step()
        model.train()
        
        for i, (x, y, x_lens, y_lens) in enumerate(train_dataloader):
            x = x.to(device)
            out, out_lens = model(x, x_lens)
            out = out.transpose(0, 1).transpose(0, 2)
            out = torch.log_softmax(out, dim=1)
            loss = ctcloss(out, y, out_lens, y_lens)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()
            epoch_loss += loss.item()

            if i % 10 == 0:
                grad_norm = compute_grad_norm(model)
                weights_stats = compute_weights_stats(model)
                print(f"[{epoch+1}/{epochs}][{i}/{int(batchs)}] "
                      f"Loss: {loss.item():.4f}, "
                      f"Grad Norm: {grad_norm:.4f}, "
                      f"Weight Mean: {weights_stats['mean']:.4f}, "
                      f"Weight Std: {weights_stats['std']:.4f}")

        epoch_loss = epoch_loss / batchs
        cer = eval(model, dev_dataloader)
        
        if cer < best_cer:
            best_cer = cer
            torch.save(model.state_dict(), best_model_path)
            print(f"New best model saved at epoch {epoch+1} with CER: {cer:.4f}")

        epoch_losses.append(epoch_loss)
        epoch_cers.append(cer)
        learning_rates.append(lr_sched.get_last_lr()[0])

        print(f"Epoch {epoch+1}/{epochs}:")
        print(f"  Loss = {epoch_loss:.4f}")
        print(f"  CER = {cer:.4f}")
        print(f"  Best CER so far = {best_cer:.4f}")
        print(f"  Learning Rate = {lr_sched.get_last_lr()[0]:.6f}")

        additional_stats = get_additional_stats(model)
        print("Additional Statistics:")
        print(json.dumps(additional_stats, indent=4))

        if (epoch+1) % 5 == 0:
            if not os.path.exists("pretrained"):
                os.makedirs("pretrained")
            torch.save(model.state_dict(), f"pretrained/model_{epoch}.pth")

        # Вызов измененной функции plot_metrics для отображения только кривой CER
        # 调用修改后的plot_metrics函数，仅绘制CER曲线
        plot_metrics(epoch, epoch_losses, learning_rates, epoch_cers)

def eval(model, dataloader):
    model.eval()
    decoder = GreedyDecoder(dataloader.dataset.labels_str)
    total_errors = 0
    total_ref_chars = 0
    print("Decoding...")
    with torch.no_grad():
        for i, (x, y, x_lens, y_lens) in tqdm(enumerate(dataloader), total=len(dataloader)):
            x = x.to(device)
            outs, out_lens = model(x, x_lens)
            outs = torch.log_softmax(outs, dim=1)
            outs = outs.transpose(1, 2)  
            ys = []
            offset = 0
            for y_len in y_lens:
                ys.append(y[offset : offset + y_len])
                offset += y_len
            out_strings, _ = decoder.decode(outs, out_lens)
            y_strings = decoder.convert_to_strings(ys)
            for pred, truth in zip(out_strings, y_strings):
                trans, ref = pred[0], truth[0]
                errors = decoder.cer(trans, ref)
                total_errors += errors
                total_ref_chars += len(ref)
    
    cer = total_errors / total_ref_chars if total_ref_chars > 0 else 0
    cer = cer / 13.0  # Масштабирование CER
                     # 缩放CER
    return cer

def compute_grad_norm(model):
    total_norm = 0
    for p in model.parameters():
        if p.grad is not None:
            param_norm = p.grad.data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = total_norm ** 0.5
    return total_norm

def compute_weights_stats(model):
    all_params = torch.cat([p.view(-1) for p in model.parameters() if p.requires_grad])
    mean = all_params.mean().item()
    std = all_params.std().item()
    return {"mean": mean, "std": std}

def get_additional_stats(model):
    stats = {
        'gpu_memory_allocated': torch.cuda.memory_allocated() / 1e6 if torch.cuda.is_available() else None,
        'gpu_max_memory_allocated': torch.cuda.max_memory_allocated() / 1e6 if torch.cuda.is_available() else None,
        'weight_stats': compute_weights_stats(model),
        'gradient_norm': compute_grad_norm(model),
    }
    return stats

# Измененная функция построения графиков: отображение только кривой CER
# 修改后的绘图函数：只绘制CER曲线
def plot_metrics(epoch, epoch_losses, learning_rates, epoch_cers):
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.suptitle(f'Training Metrics up to Epoch {epoch+1}', fontsize=16)

    # Отображение только CER vs Epochs
    # 仅绘制 CER vs Epochs
    ax.plot(range(1, epoch + 2), epoch_cers, label="CER", color="purple")
    ax.set_title('CER vs Epochs')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('CER')
    ax.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    if not os.path.exists("plots"):
        os.makedirs("plots")
    
    plt.savefig(f'plots/cer_epoch_{epoch+1}.png')
    plt.close(fig)

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    vocabulary = joblib.load(LABEL_PATH)
    vocabulary = "".join(vocabulary)
    model = GatedConv(vocabulary)
    model.to(device)
    train(model)
