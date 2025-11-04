from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("PISafeZone", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                # user_id 컬럼이 없을 때만 추가
                "SET @col_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pisafezone_data' AND COLUMN_NAME = 'user_id');"
                "SET @ddl := IF(@col_exists = 0, "
                "'ALTER TABLE `pisafezone_data` ADD COLUMN `user_id` bigint NULL', "
                "'SELECT 1');"
                "PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;"
            ),
            reverse_sql=(
                "SET @col_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pisafezone_data' AND COLUMN_NAME = 'user_id');"
                "SET @ddl := IF(@col_exists = 1, "
                "'ALTER TABLE `pisafezone_data` DROP COLUMN `user_id`', "
                "'SELECT 1');"
                "PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;"
            ),
        ),
        migrations.RunSQL(
            sql=(
                # FK가 없을 때만 추가
                "SET @fk_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pisafezone_data' AND CONSTRAINT_NAME = 'pisafezone_data_user_id_fk');"
                "SET @ddl := IF(@fk_exists = 0, "
                "'ALTER TABLE `pisafezone_data` ADD CONSTRAINT `pisafezone_data_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `pisafezone_customuser` (`id`) ON DELETE CASCADE', "
                "'SELECT 1');"
                "PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;"
            ),
            reverse_sql=(
                "SET @fk_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pisafezone_data' AND CONSTRAINT_NAME = 'pisafezone_data_user_id_fk');"
                "SET @ddl := IF(@fk_exists = 1, "
                "'ALTER TABLE `pisafezone_data` DROP FOREIGN KEY `pisafezone_data_user_id_fk`', "
                "'SELECT 1');"
                "PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;"
            ),
        ),
    ]


