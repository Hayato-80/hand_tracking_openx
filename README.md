# hand_tracking_openx

このパッケージは、MediaPipeを用いたハンドトラッキングによってROBOTISのOpenMANIPULATOR-Xロボットアームを直感的に操作するためのROS2パッケージです。

RealSenseカメラの映像上で、ユーザーの手が常に画面中央にくるようにロボットが追従します。

## 主な機能
- **ビジュアルサーボ制御**: 手の位置がカメラフレームの中央にくるように、ロボットアームが自動的に左右および上下の回転を行い、追従します。

## 動作環境要件
- Ubuntu 24.04
- ROS 2 Jazzy
- Python 3.12
- `realsense2_camera` パッケージ
- `open_manipulator` パッケージ一式

### Python 依存パッケージ
Pythonパッケージは仮想環境（`venv`）内にインストールすることを推奨します。

- `mediapipe` (v0.10.35 または Tasks API 対応バージョン)
- `opencv-python`

## インストール手順

### 1. Python仮想環境の作成
ROS 2ワークスペース内に仮想環境を作成します。

```bash
cd ~/ros2_ws
python3 -m venv --prompt ros2_ws .venv
```

### 2. 依存パッケージのインストール
仮想環境を有効化し、必要なパッケージをインストールします。

```bash
source ~/ros2_ws/.venv/bin/activate
pip install mediapipe opencv-python
```

### 3. パッケージのビルド
仮想環境のパッケージを参照できるよう、`PYTHONPATH`を設定してビルドします。

```bash
cd ~/ros2_ws
export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])'):$PYTHONPATH
colcon build --packages-select hand_tracking_openx --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

## 起動と操作手順

### 1. 環境の準備
ROS 2ワークスペースとPython仮想環境を有効化します。

```bash
cd ~/ros2_ws
source install/setup.bash
source .venv/bin/activate
export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])'):$PYTHONPATH
```

### 2. ノードの起動
以下のコマンドで必要なノードを一括起動します。

```bash
ros2 launch hand_tracking_openx hand_tracking_openx.launch.py
```

### 3. 操作方法
1. 起動後、ロボットアームが自動的に初期位置へ移動します。
2. 「Hand Tracking」ウィンドウが開き、カメラ映像と赤い十字マークが表示されます。
3. カメラに手をかざします。
4. **追従開始**: 手を「パー」の形にすると、手首の位置への追従を開始します。
5. **追従停止**: 手を「パー」以外の形にすると、追従が停止します。
6. **終了**: ターミナルで `Ctrl+C` を入力します。
