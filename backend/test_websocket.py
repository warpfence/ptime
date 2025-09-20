#!/usr/bin/env python3
"""
Socket.io WebSocket 연결 테스트 스크립트
"""

import asyncio
import socketio
import json
from datetime import datetime

# Socket.io 클라이언트 생성
sio = socketio.AsyncClient()

# 테스트 데이터
test_session_id = "test_session_123"
test_participant_id = "participant_456"
test_nickname = "테스터"

@sio.event
async def connect():
    print("✅ 서버에 연결되었습니다!")

@sio.event
async def disconnect():
    print("❌ 서버 연결이 해제되었습니다.")

@sio.event
async def connected(data):
    print(f"🔗 연결 확인: {data}")

@sio.event
async def session_joined(data):
    print(f"🎉 세션 참여 성공: {data}")

@sio.event
async def participant_joined(data):
    print(f"👤 새 참여자 참여: {data}")

@sio.event
async def participant_left(data):
    print(f"👋 참여자 나감: {data}")

@sio.event
async def participant_count_updated(data):
    print(f"📊 참여자 수 업데이트: {data}")

@sio.event
async def new_message(data):
    print(f"💬 새 메시지: {data}")

@sio.event
async def heartbeat_ack(data):
    print(f"💓 하트비트 응답: {data}")

@sio.event
async def participant_list(data):
    print(f"📋 참여자 목록: {data}")

@sio.event
async def error(data):
    print(f"❗ 오류: {data}")

async def test_websocket():
    """WebSocket 기능 테스트"""
    try:
        # 서버에 연결
        print("🔌 서버에 연결 중...")
        await sio.connect('http://localhost:8000')

        # 잠시 대기 (연결 안정화)
        await asyncio.sleep(1)

        # 세션 참여 테스트
        print("🏃 세션 참여 테스트...")
        await sio.emit('join_session', {
            'session_id': test_session_id,
            'participant_id': test_participant_id,
            'nickname': test_nickname
        })

        await asyncio.sleep(2)

        # 참여자 목록 조회 테스트
        print("📝 참여자 목록 조회 테스트...")
        await sio.emit('get_participant_list', {})

        await asyncio.sleep(1)

        # 메시지 전송 테스트
        print("💌 메시지 전송 테스트...")
        await sio.emit('send_message', {
            'message': '안녕하세요! 테스트 메시지입니다.'
        })

        await asyncio.sleep(1)

        # 하트비트 테스트
        print("💗 하트비트 테스트...")
        await sio.emit('heartbeat', {})

        await asyncio.sleep(1)

        # 세션 나가기 테스트
        print("🚪 세션 나가기 테스트...")
        await sio.emit('leave_session', {})

        await asyncio.sleep(2)

        # 연결 해제
        print("🔌 연결 해제...")
        await sio.disconnect()

        print("✅ 모든 테스트 완료!")

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

async def test_multiple_clients():
    """다중 클라이언트 연결 테스트"""
    print("👥 다중 클라이언트 테스트 시작...")

    clients = []
    for i in range(3):
        client = socketio.AsyncClient()

        @client.event
        async def connect():
            print(f"✅ 클라이언트 {i+1} 연결됨")

        @client.event
        async def participant_joined(data):
            print(f"👤 클라이언트 {i+1}이 새 참여자 감지: {data['nickname']}")

        await client.connect('http://localhost:8000')

        # 세션 참여
        await client.emit('join_session', {
            'session_id': test_session_id,
            'participant_id': f'participant_{i+1}',
            'nickname': f'테스터{i+1}'
        })

        clients.append(client)
        await asyncio.sleep(0.5)

    # 잠시 대기
    await asyncio.sleep(3)

    # 모든 클라이언트 연결 해제
    for i, client in enumerate(clients):
        await client.emit('leave_session', {})
        await client.disconnect()
        print(f"❌ 클라이언트 {i+1} 연결 해제")
        await asyncio.sleep(0.5)

    print("✅ 다중 클라이언트 테스트 완료!")

if __name__ == "__main__":
    print("🚀 Socket.io WebSocket 테스트 시작\n")

    # 단일 클라이언트 테스트
    print("=== 단일 클라이언트 테스트 ===")
    asyncio.run(test_websocket())

    print("\n" + "="*50 + "\n")

    # 다중 클라이언트 테스트
    print("=== 다중 클라이언트 테스트 ===")
    asyncio.run(test_multiple_clients())

    print("\n🎉 모든 테스트 완료!")