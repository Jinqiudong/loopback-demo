from setuptools import setup, find_packages

setup(
    name="knowledge_vault",
    version="0.1.0",
    packages=find_packages(include=["knowledge_vault"]),
    install_requires=[
        "supabase>=2.0.0",
        "openai>=1.0.0",
    ],
    python_requires=">=3.9",
)
