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

### 1. Python仮想環境（venv）の作成
colconのビルドプロセスと競合しないよう、`ros2_ws`内に`venv`を作成します。

```bash
cd ~/ros2_ws
python3 -m venv --prompt ros2_ws .venv
```

### 2. Python依存関係のインストール
作成した仮想環境を有効化し、MediaPipeとOpenCVをインストールします。

```bash
source ~/ros2_ws/.venv/bin/activate
pip install mediapipe opencv-python
```

### 3. パッケージのビルド
ビルドおよび実行時に仮想環境のパッケージを参照できるように、`PYTHONPATH` を設定してからビルドを行います。

```bash
cd ~/ros2_ws
export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])'):$PYTHONPATH
colcon build --packages-select hand_tracking_openx --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

## 起動と操作手順

### 1. 環境の準備
起動前に、必ずROS 2ワークスペースとPython仮想環境の両方を読み込んでください。

```bash
cd ~/ros2_ws
source install/setup.bash
source .venv/bin/activate
export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])'):$PYTHONPATH
```

### 2. ノードの起動
以下のLaunchファイルを実行すると、OpenMANIPULATOR-Xのコントローラ、RealSenseカメラのノード、およびハンドトラッキングノードがすべて自動で立ち上がります。

```bash
ros2 launch hand_tracking_openx hand_tracking_openx.launch.py
```

### 3. 操作方法
1. システムが起動すると、ロボットアームが自動的に初期位置に移動します。
2. 「Hand Tracking」というウィンドウが開き、カメラの映像と中央に赤い十字マークが表示されます。
3. カメラに手をかざします。
4. **【追従開始】**: 手を「パー」の形にしてください。ロボットが赤い十字マークを手首の位置に合わせるように滑らかに動き出します。
5. **【追従停止】**: 手のジェスチャーが「パー」以外だとロボットの追従が停止します。
6. **【終了方法】**: ターミナル上で `Ctrl+C`を押してください。
