#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import wave
import struct
import math
import random
import argparse

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def generate_pn_sequence(seed_val, length):
    """
    Sinh chuỗi mã giả ngẫu nhiên PN sử dụng LFSR 10-bit (taps ở vị trí 9 và 2)
    tương tự như bài lab trước để đảm bảo tính nhất quán.
    """
    reg = seed_val & 0x3FF
    if reg == 0:
        reg = 1
    pn = []
    for _ in range(length):
        b9 = (reg >> 9) & 1
        b2 = (reg >> 2) & 1
        fb = b9 ^ b2
        reg = ((reg << 1) & 0x3FF) | fb
        pn.append(1 if fb == 1 else -1)
    return pn

def generate_hopping_sequence(seed_val, length):
    """
    Sinh chuỗi nhảy tần số (hopping sequence) từ seed sử dụng LFSR.
    Trả về danh sách các chỉ số kênh từ 0 đến 7.
    """
    reg = seed_val & 0x3FF
    if reg == 0:
        reg = 1
    hops = []
    for _ in range(length):
        val = 0
        for _ in range(3):  # Lấy 3 bit từ LFSR để sinh số từ 0-7
            b9 = (reg >> 9) & 1
            b2 = (reg >> 2) & 1
            fb = b9 ^ b2
            reg = ((reg << 1) & 0x3FF) | fb
            val = (val << 1) | fb
        hops.append(val % 8)
    return hops

def read_wav(filename):
    """Đọc file WAV 16-bit Mono và chuẩn hóa biên độ về khoảng [-1.0, 1.0]"""
    with wave.open(filename, 'rb') as wav:
        params = wav.getparams()
        nframes = wav.getnframes()
        frames = wav.readframes(nframes)
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            print("Lỗi: Chỉ hỗ trợ file WAV 16-bit Mono!")
            sys.exit(1)
        samples = list(struct.unpack(f'<{nframes}h', frames))
        float_samples = [s / 32768.0 for s in samples]
        return float_samples, params

def write_wav(filename, float_samples, params):
    """Lưu danh sách mẫu âm thanh dạng float vào file WAV 16-bit Mono"""
    with wave.open(filename, 'wb') as wav:
        wav.setparams(params)
        int_samples = []
        for s in float_samples:
            ival = int(s * 32767.0)
            ival = max(-32768, min(32767, ival))
            int_samples.append(ival)
        frames = struct.pack(f'<{len(int_samples)}h', *int_samples)
        wav.writeframes(frames)

# ---------------------------------------------------------
# DSSS Steganography Logic
# ---------------------------------------------------------
def embed_dsss(cover_samples, message_str, seed_val, alpha):
    bits = []
    for char in message_str:
        val = ord(char)
        for i in range(7, -1, -1):
            bits.append((val >> i) & 1)
            
    d = [1 if b == 1 else -1 for b in bits]
    pn = generate_pn_sequence(seed_val, 1023)
    
    s = []
    for di in d:
        for p in pn:
            s.append(di * p)
            
    stego_samples = list(cover_samples)
    for k in range(len(s)):
        idx = k + 1000
        if idx >= len(stego_samples):
            break
        stego_samples[idx] = max(-1.0, min(1.0, cover_samples[idx] + alpha * s[k]))
        
    return stego_samples

def extract_dsss(stego_samples, num_bits, seed_val):
    pn = generate_pn_sequence(seed_val, 1023)
    recovered_bits = []
    for i in range(num_bits):
        start_idx = 1000 + i * 1023
        end_idx = start_idx + 1023
        if end_idx > len(stego_samples):
            break
        r_i = stego_samples[start_idx:end_idx]
        corr = sum(r_i[j] * pn[j] for j in range(1023))
        recovered_bits.append(1 if corr > 0 else 0)
        
    chars = []
    for i in range(0, len(recovered_bits), 8):
        byte = recovered_bits[i:i+8]
        if len(byte) < 8:
            break
        val = 0
        for b in byte:
            val = (val << 1) | b
        chars.append(chr(val))
    return "".join(chars)

# ---------------------------------------------------------
# FHSS Steganography Logic
# ---------------------------------------------------------
# Định nghĩa 8 tần số sóng mang (carrier frequencies) khả dụng từ 1000 Hz đến 4500 Hz
FHSS_FREQUENCIES = [1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500]

def embed_fhss(cover_samples, message_str, seed_val, alpha):
    bits = []
    for char in message_str:
        val = ord(char)
        for i in range(7, -1, -1):
            bits.append((val >> i) & 1)
            
    d = [1 if b == 1 else -1 for b in bits]
    hops = generate_hopping_sequence(seed_val, len(d))
    
    stego_samples = list(cover_samples)
    for i in range(len(d)):
        start_idx = 1000 + i * 1023
        freq = FHSS_FREQUENCIES[hops[i]]
        
        for j in range(1023):
            idx = start_idx + j
            if idx >= len(stego_samples):
                break
            # Tạo tín hiệu sóng mang nhảy tần
            carrier = math.sin(2 * math.pi * freq * j / 44100.0)
            stego_samples[idx] = max(-1.0, min(1.0, cover_samples[idx] + alpha * d[i] * carrier))
            
    return stego_samples

def extract_fhss(stego_samples, num_bits, seed_val):
    hops = generate_hopping_sequence(seed_val, num_bits)
    recovered_bits = []
    
    for i in range(num_bits):
        start_idx = 1000 + i * 1023
        freq = FHSS_FREQUENCIES[hops[i]]
        
        corr = 0
        for j in range(1023):
            idx = start_idx + j
            if idx >= len(stego_samples):
                break
            carrier = math.sin(2 * math.pi * freq * j / 44100.0)
            corr += stego_samples[idx] * carrier
            
        recovered_bits.append(1 if corr > 0 else 0)
        
    chars = []
    for i in range(0, len(recovered_bits), 8):
        byte = recovered_bits[i:i+8]
        if len(byte) < 8:
            break
        val = 0
        for b in byte:
            val = (val << 1) | b
        chars.append(chr(val))
    return "".join(chars)

# ---------------------------------------------------------
# Analysis and Noise Tools
# ---------------------------------------------------------
def calculate_snr(cover_samples, stego_samples):
    """Tính toán tỷ số tín hiệu trên nhiễu SNR (dB)"""
    p_signal = sum(x**2 for x in cover_samples)
    p_noise = sum((y - x)**2 for x, y in zip(cover_samples, stego_samples))
    if p_noise == 0:
        return float('inf')
    return 10 * math.log10(p_signal / p_noise)

def add_wgn(samples, variance):
    """Thêm nhiễu trắng Gaussian (Wideband Noise)"""
    noisy = []
    std_dev = math.sqrt(variance)
    for s in samples:
        noise = random.gauss(0, std_dev)
        noisy.append(max(-1.0, min(1.0, s + noise)))
    return noisy

def add_jamming(samples, frequency, amplitude):
    """Thêm nhiễu đơn tần cực mạnh (Narrowband Jamming)"""
    jammed = []
    for i, s in enumerate(samples):
        # Tạo tín hiệu nhiễu liên tục hình sin
        jam = amplitude * math.sin(2 * math.pi * frequency * i / 44100.0)
        jammed.append(max(-1.0, min(1.0, s + jam)))
    return jammed

# ---------------------------------------------------------
# Command Line Interface (CLI)
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Steganography Tool - Compare DSSS & FHSS")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: embed-dsss
    parser_emb_d = subparsers.add_parser("embed-dsss", help="Nhúng thông điệp bằng DSSS")
    parser_emb_d.add_argument("--cover", type=str, required=True, help="File cover.wav")
    parser_emb_d.add_argument("--message", type=str, required=True, help="Thông điệp bí mật")
    parser_emb_d.add_argument("--seed", type=int, required=True, help="Seed khóa mật")
    parser_emb_d.add_argument("--alpha", type=float, default=0.005, help="Hệ số alpha")
    parser_emb_d.add_argument("--out", type=str, required=True, help="File stego_dsss.wav đầu ra")

    # Command: embed-fhss
    parser_emb_f = subparsers.add_parser("embed-fhss", help="Nhúng thông điệp bằng FHSS")
    parser_emb_f.add_argument("--cover", type=str, required=True, help="File cover.wav")
    parser_emb_f.add_argument("--message", type=str, required=True, help="Thông điệp bí mật")
    parser_emb_f.add_argument("--seed", type=int, required=True, help="Seed khóa mật")
    parser_emb_f.add_argument("--alpha", type=float, default=0.005, help="Hệ số alpha")
    parser_emb_f.add_argument("--out", type=str, required=True, help="File stego_fhss.wav đầu ra")

    # Command: extract-dsss
    parser_ext_d = subparsers.add_parser("extract-dsss", help="Trích xuất thông điệp DSSS")
    parser_ext_d.add_argument("--stego", type=str, required=True, help="File stego_dsss.wav")
    parser_ext_d.add_argument("--bits", type=int, default=56, help="Số bit cần trích xuất")
    parser_ext_d.add_argument("--seed", type=int, required=True, help="Seed khóa mật")
    parser_ext_d.add_argument("--out", type=str, required=True, help="File văn bản kết quả")

    # Command: extract-fhss
    parser_ext_f = subparsers.add_parser("extract-fhss", help="Trích xuất thông điệp FHSS")
    parser_ext_f.add_argument("--stego", type=str, required=True, help="File stego_fhss.wav")
    parser_ext_f.add_argument("--bits", type=int, default=56, help="Số bit cần trích xuất")
    parser_ext_f.add_argument("--seed", type=int, required=True, help="Seed khóa mật")
    parser_ext_f.add_argument("--out", type=str, required=True, help="File văn bản kết quả")

    # Command: snr
    parser_snr = subparsers.add_parser("snr", help="Tính toán tỷ số SNR")
    parser_snr.add_argument("--cover", type=str, required=True, help="File cover.wav")
    parser_snr.add_argument("--stego", type=str, required=True, help="File stego.wav")
    parser_snr.add_argument("--out", type=str, required=True, help="File lưu tỷ lệ SNR")

    # Command: add-wgn
    parser_wgn = subparsers.add_parser("add-wgn", help="Thêm nhiễu trắng Gaussian")
    parser_wgn.add_argument("--stego", type=str, required=True, help="File stego.wav")
    parser_wgn.add_argument("--variance", type=float, required=True, help="Phương sai nhiễu")
    parser_wgn.add_argument("--out", type=str, required=True, help="File stego_noisy.wav đầu ra")

    # Command: add-jam
    parser_jam = subparsers.add_parser("add-jam", help="Thêm nhiễu đơn tần đơn trị (Jamming)")
    parser_jam.add_argument("--stego", type=str, required=True, help="File stego.wav")
    parser_jam.add_argument("--frequency", type=float, default=2000.0, help="Tần số nhiễu (Hz)")
    parser_jam.add_argument("--amplitude", type=float, default=0.2, help="Biên độ nhiễu")
    parser_jam.add_argument("--out", type=str, required=True, help="File stego_jammed.wav đầu ra")

    args = parser.parse_args()

    if args.command == "embed-dsss":
        cover, params = read_wav(args.cover)
        stego = embed_dsss(cover, args.message, args.seed, args.alpha)
        write_wav(args.out, stego, params)
        print(f"[DSSS] Đã nhúng thành công và lưu vào {args.out}")

    elif args.command == "embed-fhss":
        cover, params = read_wav(args.cover)
        stego = embed_fhss(cover, args.message, args.seed, args.alpha)
        write_wav(args.out, stego, params)
        print(f"[FHSS] Đã nhúng thành công và lưu vào {args.out}")

    elif args.command == "extract-dsss":
        stego, _ = read_wav(args.stego)
        recovered = extract_dsss(stego, args.bits, args.seed)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(recovered + "\n")
        print(f"[DSSS] Đã trích xuất thông điệp và lưu vào {args.out}: '{recovered}'")

    elif args.command == "extract-fhss":
        stego, _ = read_wav(args.stego)
        recovered = extract_fhss(stego, args.bits, args.seed)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(recovered + "\n")
        print(f"[FHSS] Đã trích xuất thông điệp và lưu vào {args.out}: '{recovered}'")

    elif args.command == "snr":
        cover, _ = read_wav(args.cover)
        stego, _ = read_wav(args.stego)
        snr = calculate_snr(cover, stego)
        with open(args.out, "w") as f:
            f.write(f"{snr:.2f}\n")
        print(f"SNR: {snr:.2f} dB (Đã lưu vào {args.out})")

    elif args.command == "add-wgn":
        stego, params = read_wav(args.stego)
        noisy = add_wgn(stego, args.variance)
        write_wav(args.out, noisy, params)
        print(f"Đã thêm nhiễu trắng Gaussian (var={args.variance}) và lưu vào {args.out}")

    elif args.command == "add-jam":
        stego, params = read_wav(args.stego)
        jammed = add_jamming(stego, args.frequency, args.amplitude)
        write_wav(args.out, jammed, params)
        print(f"Đã thêm nhiễu đơn tần ({args.frequency} Hz, amp={args.amplitude}) và lưu vào {args.out}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
