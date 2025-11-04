from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("PISafeZone", "0002_fix_data_user_column"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                # 사용 이력 테이블이 없을 때만 생성
                "SET @tbl_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pisafezone_usagehistory');"
                "SET @ddl := IF(@tbl_exists = 0, "
                "'CREATE TABLE `pisafezone_usagehistory` ("
                "`usage_id` char(32) NOT NULL,"
                "`usage_type` varchar(10) NOT NULL,"
                "`used_at` datetime(6) NOT NULL,"
                "`data_id` char(32) NOT NULL,"
                "`user_id` bigint NOT NULL,"
                "PRIMARY KEY (`usage_id`),"
                "KEY `pisafezone_usagehistory_data_id_idx` (`data_id`),"
                "KEY `pisafezone_usagehistory_user_id_idx` (`user_id`),"
                "CONSTRAINT `pisafezone_usagehistory_data_id_fk` FOREIGN KEY (`data_id`) REFERENCES `pisafezone_data` (`data_id`) ON DELETE CASCADE,"
                "CONSTRAINT `pisafezone_usagehistory_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `pisafezone_customuser` (`id`) ON DELETE CASCADE"
                ")', "
                "'SELECT 1');"
                "PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;"
            ),
            reverse_sql=(
                "SET @tbl_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pisafezone_usagehistory');"
                "SET @ddl := IF(@tbl_exists = 1, "
                "'DROP TABLE `pisafezone_usagehistory`', "
                "'SELECT 1');"
                "PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;"
            ),
        )
    ]


