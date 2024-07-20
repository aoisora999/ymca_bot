import speedtest
import aiohttp
import asyncio

async def get_ping():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://google.com') as response:
                if response.status == 200:
                    return response.elapsed.total_seconds() * 1000
    except Exception as e:
        return str(e)

async def run_speed_test(download=True, upload=True, ping=False):
    st = speedtest.Speedtest()
    st.get_best_server()
    results = ""

    try:
        if download:
            download_speed = st.download() / 1_000_000
            results += f"Download speed: {download_speed:.2f} Mbps\n\n"
    except Exception as e:
        results += f"Error measuring download speed: {e}\n\n"

    try:
        if upload:
            upload_speed = st.upload() / 1_000_000
            results += f"Upload speed: {upload_speed:.2f} Mbps\n"
    except Exception as e:
        results += f"Error measuring upload speed: {e}\n"

    if ping:
        ping_time = await get_ping()
        if isinstance(ping_time, str):
            results += f"Error measuring ping time: {ping_time}\n"
        else:
            results += f"Ping time: {ping_time:.2f} ms\n"

    return results.strip()