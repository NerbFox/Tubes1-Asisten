[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# 💎 Etimo Diamonds 2

Diamonds is a programming challenge. Program a bot and compete to get the highest score. For more information:

-   [Project Specification](https://docs.google.com/document/d/13cbmMVXviyu8eKQ6heqgDzt4JNNMeAZO/edit)
-   [Get Started with Diamonds](https://docs.google.com/document/d/1L92Axb89yIkom0b24D350Z1QAr8rujvHof7-kXRAp7c/edit)

## Installing Dependencies 🔨

1. Clone this repository and move to the root of this project's directory

    ```
    git clone https://github.com/haziqam/tubes1-IF2110-bot-starter-pack.git
    cd ./tubes1-IF2110-bot-starter-pack
    ```

2. Install dependencies

    ```
    pip install -r requirements.txt
    ```

## How to Run 💻

1. To run one bot

    ```
    python main.py --logic Random --email=your_email@example.com --name=your_name --password=your_password --team etimo
    ```

2. To run multiple bots simultaneously

    For Windows

    ```
    ./run-bots.bat
    ```

    For Linux / (possibly) macOS

    ```
    ./run-bots.sh
    ```

    <b>Before executing the script, make sure to change the permission of the shell script to enable executing the script (for linux/macOS)</b>

    ```
    chmod +x run-bots.sh
    ```

#### Note:

-   If you run multiple bots, make sure each emails and names are unique
-   The email could be anything as long as it follows a correct email syntax
-   The name, and password could be anything without any space

## Credits 🪙

This repository is adapted from https://github.com/Etimo/diamonds2

Some code in this repository is adjusted to fix some issues in the original repository and to adapt to the requirements of Algorithm Strategies course (IF2211), Informatics Undergraduate Program, ITB.

©️ All rights and credits reserved to [Etimo](https://github.com/Etimo)
