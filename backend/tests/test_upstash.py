import os
import asyncio
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

async def test_redis():
    host = os.getenv("REDIS_HOST")
    port = int(os.getenv("REDIS_PORT", 6379))
    password = os.getenv("REDIS_PASSWORD")
    use_ssl = os.getenv("REDIS_SSL", "False").lower() == "true" or "upstash.io" in host
    
    print("=" * 60)
    print("UPSTASH REDIS CONNECTION TEST")
    print("=" * 60)
    print(f"Host:     {host}")
    print(f"Port:     {port}")
    print(f"SSL:      {use_ssl}")
    print(f"Password: {'*' * len(password) if password else 'NONE'}")
    print("=" * 60)
    
    try:
        client_kwargs = {
            "host": host,
            "port": port,
            "password": password,
            "decode_responses": True,
            "socket_timeout": 10,
            "socket_connect_timeout": 10,
        }
        
        if use_ssl:
            client_kwargs["ssl"] = True
            client_kwargs["ssl_cert_reqs"] = "required"
        
        if "upstash.io" in host:
            client_kwargs["username"] = "default"
        
        print("\n🔌 Connecting...")
        client = redis.Redis(**client_kwargs)
        
        pong = await client.ping()
        print(f"✅ PING: {pong}")
        
        await client.set("chronos:test", "hello", ex=60)
        value = await client.get("chronos:test")
        print(f"✅ SET/GET: {value}")
        
        info = await client.info("server")
        print(f"✅ Redis Version: {info.get('redis_version')}")
        print(f"✅ Connected Clients: {info.get('connected_clients')}")
        
        await client.delete("chronos:test")
        print("✅ DELETE: OK")
        
        await client.aclose()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED — UPSTASH IS WORKING!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("\n" + "=" * 60)
        print("TROUBLESHOOTING:")
        print("=" * 60)
        print("1. Verify REDIS_HOST is correct (should end with .upstash.io)")
        print("2. Verify REDIS_PASSWORD is the long string from Upstash")
        print("3. Verify REDIS_SSL=True in .env")
        print("4. Check Upstash console — is the DB active?")
        print("=" * 60)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis())