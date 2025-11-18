# 1. Base Image (Python 3.10 Slim - হালকা এবং ফাস্ট)
FROM python:3.10-slim

# 2. Environment Variables সেট করা (Python এর জন্য ভালো প্র্যাকটিস)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. কন্টেইনারের ভেতর ফোল্ডার তৈরি করা
WORKDIR /app

# 4. হেলথ চেকের জন্য curl ইন্সটল করা (Optional but Pro feature)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 5. Requirements ফাইল কপি এবং ইন্সটল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. বাকি সব প্রজেক্ট ফাইল কপি করা
COPY . .

# 7. Streamlit এর ডিফল্ট পোর্ট ওপেন করা
EXPOSE 8501

# 8. হেলথ চেক (অ্যাপ ঠিকমতো চলছে কিনা চেক করবে)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 9. অ্যাপ রান করার কমান্ড
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
