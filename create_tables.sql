-- 1. Удаляем ВСЁ в правильном порядке с CASCADE
DROP TABLE IF EXISTS shift_assignments CASCADE;
DROP TABLE IF EXISTS leave_records CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS shifts CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 2. Пользователи
CREATE TABLE users (
    telegram_tag TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    role TEXT CHECK (role IN ('employee', 'supervisor', 'hr')) NOT NULL,
    status TEXT DEFAULT 'on_shift' CHECK (status IN ('on_shift', 'on_vacation', 'available'))
);

-- 3. Смены
CREATE TABLE shifts (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    supervisor_telegram_tag TEXT REFERENCES users(telegram_tag) ON DELETE SET NULL
);

-- 4. Назначения (многие-ко-многим)
CREATE TABLE shift_assignments (
    user_telegram_tag TEXT REFERENCES users(telegram_tag) ON DELETE CASCADE,
    shift_id INTEGER REFERENCES shifts(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_telegram_tag, shift_id)
);

-- 5. События
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    reporter_telegram_tag TEXT NOT NULL REFERENCES users(telegram_tag) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Отпуска
CREATE TABLE leave_records (
    id SERIAL PRIMARY KEY,
    user_telegram_tag TEXT NOT NULL REFERENCES users(telegram_tag) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    type TEXT CHECK (type IN ('vacation', 'sick', 'absent')) DEFAULT 'vacation',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Синтетические данные (опционально, можно вынести в отдельный файл)
INSERT INTO users (telegram_tag, full_name, role, status) VALUES
('@Boryakov', 'Boryakov N.A.', 'hr', 'on_vacation'),
('@Sunrise_ne_yveren', 'Sunrise', 'employee', 'on_vacation'),
('@sstasbaldanov', 'Stanislav Boldanov', 'employee', 'on_shift'),
('@smtg_wrong', 'Orlov Andrew', 'supervisor', 'on_shift'),
('@test', 'Test User', 'employee', 'available');

INSERT INTO leave_records (user_telegram_tag, start_date, end_date, type)
VALUES ('@Sunrise_ne_yveren', '2025-11-20', '2025-11-25', 'vacation');

INSERT INTO events (description, reporter_telegram_tag, created_at) VALUES
('Остановка конвейера №3', '@sstasbaldanov', '2025-11-22 08:15:00+07'),
('Утечка масла в пресс-цеху', '@sstasbaldanov', '2025-11-22 10:30:00+07'),
('Неисправность датчика температуры', '@sstasbaldanov', '2025-11-22 12:45:00+07');

INSERT INTO shifts (date, supervisor_telegram_tag)
VALUES ('2025-11-22', '@smtg_wrong');

INSERT INTO shift_assignments (user_telegram_tag, shift_id) VALUES
('@sstasbaldanov', 1),
('@test', 1);