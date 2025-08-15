FROM node:18-alpine

# Создание рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apk add --no-cache git

# Копирование package.json и yarn.lock
COPY package.json yarn.lock ./

# Установка зависимостей
RUN yarn install --frozen-lockfile

# Копирование исходного кода
COPY . .

# Экспорт порта
EXPOSE 3000

# Команда запуска в режиме разработки
CMD ["yarn", "start"]