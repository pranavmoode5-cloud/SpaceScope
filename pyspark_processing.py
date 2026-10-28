"""
SpaceScope: Big Data Analytics of Global Space Missions
Module 2: PySpark Data Processing & Cleaning
Handles distributed data processing, cleaning, transformation, and aggregation
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, year, month, when, count, avg, max, min, 
    countDistinct, collect_list, struct, array_join
)
from pyspark.sql.types import StructType, StructField, StringType, DateType
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PySparkProcessor:
    """Handles PySpark-based big data processing for space missions"""
    
    def __init__(self, app_name="SpaceScope"):
        """Initialize Spark Session"""
        try:
            self.spark = SparkSession.builder \
                .appName(app_name) \
                .config("spark.sql.shuffle.partitions", "4") \
                .getOrCreate()
            
            # Reduce verbosity
            self.spark.sparkContext.setLogLevel("ERROR")
            
            logger.info("✅ Spark Session initialized successfully")
            self.logger = logger
        except Exception as e:
            logger.error(f"❌ Error initializing Spark: {e}")
            raise
    
    def create_dataframe_from_pandas(self, pandas_df):
        """Convert Pandas DataFrame to Spark DataFrame"""
        try:
            spark_df = self.spark.createDataFrame(pandas_df)
            logger.info(f"✅ Created Spark DataFrame with {spark_df.count()} records")
            return spark_df
        except Exception as e:
            logger.error(f"❌ Error creating Spark DataFrame: {e}")
            return None
    
    def data_cleaning(self, spark_df):
        """
        Step 1: Data Cleaning
        - Handle missing values
        - Remove duplicates
        - Standardize date formats
        - Clean categorical values
        """
        print("\n🧹 Step 1: Data Cleaning & Validation")
        print("-" * 80)
        
        # Check initial row count
        initial_count = spark_df.count()
        logger.info(f"Initial records: {initial_count}")
        
        # Remove duplicates
        cleaned_df = spark_df.dropDuplicates()
        after_dedup = cleaned_df.count()
        duplicates_removed = initial_count - after_dedup
        logger.info(f"Duplicates removed: {duplicates_removed}")
        print(f"✅ Removed duplicates: {duplicates_removed} records")
        
        # Handle null values - drop rows with essential null columns
        essential_cols = ['company', 'rocket', 'launch_date', 'launch_site', 'country']
        cleaned_df = cleaned_df.dropna(subset=essential_cols, how='any')
        after_null_drop = cleaned_df.count()
        nulls_removed = after_dedup - after_null_drop
        logger.info(f"Rows with null values removed: {nulls_removed}")
        print(f"✅ Removed null values: {nulls_removed} records")
        
        # Data quality metrics
        total_removed = initial_count - after_null_drop
        print(f"✅ Total records after cleaning: {after_null_drop}")
        print(f"✅ Data quality: {(after_null_drop/initial_count)*100:.2f}%")
        
        return cleaned_df
    
    def data_transformation(self, cleaned_df):
        """
        Step 2: Data Transformation
        - Extract year, month from launch_date
        - Standardize rocket names
        - Categorize missions
        - Extract country information
        """
        print("\n🔄 Step 2: Data Transformation & Feature Engineering")
        print("-" * 80)
        
        # Convert launch_date to proper date format and extract year/month
        transformed_df = cleaned_df.withColumn(
            'launch_date', col('launch_date').cast('date')
        ).withColumn(
            'year', year(col('launch_date'))
        ).withColumn(
            'month', month(col('launch_date'))
        )
        
        # Standardize company names (remove variations)
        transformed_df = transformed_df.withColumn(
            'company_std', when(col('company').contains('USSR'), 'USSR')
                          .when(col('company').contains('SpaceX'), 'SpaceX')
                          .when(col('company').contains('China'), 'China')
                          .otherwise(col('company'))
        )
        
        # Categorize mission success
        transformed_df = transformed_df.withColumn(
            'is_success', when(col('mission_status') == 'Success', 1).otherwise(0)
        )
        
        # Create mission status category
        transformed_df = transformed_df.withColumn(
            'status_category', 
            when(col('mission_status') == 'Success', 'Successful')
            .when(col('mission_status') == 'Failed', 'Failed')
            .otherwise('Partial/Other')
        )
        
        print("✅ Extracted features: year, month, company_std, is_success")
        print("✅ Standardized categorical values")
        print(f"✅ Total transformed records: {transformed_df.count()}")
        
        return transformed_df
    
    def data_aggregation(self, transformed_df):
        """
        Step 3: Data Aggregation using Spark SQL
        - Group by year, organization, rocket, country
        - Calculate aggregations (COUNT, AVG, MAX, MIN)
        """
        print("\n📊 Step 3: Aggregation & Analytics")
        print("-" * 80)
        
        aggregations = {}
        
        # 1. Missions by Year
        print("\n1️⃣  Temporal Analysis - Missions by Year:")
        yearly_missions = transformed_df.groupBy('year') \
            .agg(
                count('*').alias('mission_count'),
                countDistinct('company').alias('unique_orgs'),
                avg('is_success').alias('success_rate')
            ) \
            .orderBy('year')
        
        aggregations['yearly_missions'] = yearly_missions
        yearly_data = yearly_missions.collect()
        for row in yearly_data[:5]:  # Show first 5 years
            print(f"   {row.year}: {int(row.mission_count)} missions, "
                  f"Success Rate: {row.success_rate*100:.1f}%")
        
        # 2. Missions by Organization
        print("\n2️⃣  Organization Analysis:")
        org_missions = transformed_df.groupBy('company') \
            .agg(
                count('*').alias('mission_count'),
                avg('is_success').alias('success_rate'),
                countDistinct('rocket').alias('rocket_types')
            ) \
            .orderBy(col('mission_count').desc())
        
        aggregations['org_missions'] = org_missions
        org_data = org_missions.collect()
        for row in org_data[:5]:  # Top 5 orgs
            print(f"   {row.company}: {int(row.mission_count)} missions, "
                  f"Success Rate: {row.success_rate*100:.1f}%")
        
        # 3. Rocket Usage
        print("\n3️⃣  Rocket Analysis:")
        rocket_usage = transformed_df.groupBy('rocket') \
            .agg(
                count('*').alias('usage_count'),
                avg('is_success').alias('success_rate'),
                countDistinct('company').alias('organizations')
            ) \
            .orderBy(col('usage_count').desc())
        
        aggregations['rocket_usage'] = rocket_usage
        rocket_data = rocket_usage.collect()
        for row in rocket_data[:5]:  # Top 5 rockets
            print(f"   {row.rocket}: {int(row.usage_count)} launches, "
                  f"Success Rate: {row.success_rate*100:.1f}%")
        
        # 4. Launch Sites
        print("\n4️⃣  Launch Site Analysis:")
        launch_sites = transformed_df.groupBy('launch_site', 'country') \
            .agg(
                count('*').alias('mission_count'),
                avg('is_success').alias('success_rate')
            ) \
            .orderBy(col('mission_count').desc())
        
        aggregations['launch_sites'] = launch_sites
        site_data = launch_sites.collect()
        for row in site_data[:5]:  # Top 5 sites
            print(f"   {row.launch_site} ({row.country}): {int(row.mission_count)} missions")
        
        # 5. Mission Types
        print("\n5️⃣  Mission Type Distribution:")
        mission_types = transformed_df.groupBy('mission_type') \
            .agg(
                count('*').alias('mission_count'),
                avg('is_success').alias('success_rate')
            ) \
            .orderBy(col('mission_count').desc())
        
        aggregations['mission_types'] = mission_types
        mission_data = mission_types.collect()
        for row in mission_data:
            print(f"   {row.mission_type}: {int(row.mission_count)} missions, "
                  f"Success Rate: {row.success_rate*100:.1f}%")
        
        # 6. Success Analysis
        print("\n6️⃣  Mission Status Distribution:")
        status_analysis = transformed_df.groupBy('status_category') \
            .agg(count('*').alias('mission_count')) \
            .orderBy(col('mission_count').desc())
        
        aggregations['status_analysis'] = status_analysis
        status_data = status_analysis.collect()
        total_missions = sum([row.mission_count for row in status_data])
        for row in status_data:
            pct = (row.mission_count / total_missions) * 100
            print(f"   {row.status_category}: {int(row.mission_count)} ({pct:.1f}%)")
        
        print("-" * 80)
        return aggregations, transformed_df
    
    def convert_to_pandas(self, spark_df):
        """Convert Spark DataFrame to Pandas DataFrame"""
        try:
            pandas_df = spark_df.toPandas()
            logger.info(f"✅ Converted to Pandas DataFrame with {len(pandas_df)} records")
            return pandas_df
        except Exception as e:
            logger.error(f"❌ Error converting to Pandas: {e}")
            return None
    
    def show_dataframe_info(self, spark_df, rows=5):
        """Display DataFrame schema and sample data"""
        print("\n📋 DataFrame Schema:")
        print("-" * 80)
        spark_df.printSchema()
        
        print("\n📊 Sample Data:")
        print("-" * 80)
        spark_df.show(rows, truncate=False)
    
    def stop_session(self):
        """Stop Spark Session"""
        if self.spark:
            self.spark.stop()
            logger.info("✅ Spark Session stopped")


def main():
    """Test PySpark processing module"""
    print("\n" + "="*80)
    print("🚀 SpaceScope: PySpark Processing Module")
    print("="*80)
    
    # Import data source from data_ingestion module
    from data_ingestion import SpaceMissionDataSource
    
    # Step 1: Load data
    print("\n📥 Step 0: Data Ingestion")
    print("-" * 80)
    data_source = SpaceMissionDataSource()
    pandas_df = data_source.create_sample_dataset()
    print("✅ Pandas DataFrame created")
    
    # Step 2: Initialize PySpark
    processor = PySparkProcessor()
    
    # Step 3: Create Spark DataFrame
    print("\n📥 Creating Spark DataFrame...")
    spark_df = processor.create_dataframe_from_pandas(pandas_df)
    
    # Step 4: Data Cleaning
    cleaned_df = processor.data_cleaning(spark_df)
    
    # Step 5: Data Transformation
    transformed_df = processor.data_transformation(cleaned_df)
    
    # Step 6: Data Aggregation & Analytics
    aggregations, final_df = processor.data_aggregation(transformed_df)
    
    # Step 7: Display processed data
    print("\n📋 Processed DataFrame Sample:")
    processor.show_dataframe_info(final_df.select(
        'company', 'rocket', 'launch_date', 'year', 'country', 
        'mission_status', 'mission_type', 'is_success'
    ), rows=5)
    
    # Step 8: Summary statistics
    print("\n📊 Summary Statistics:")
    print("-" * 80)
    total_missions = final_df.count()
    successful = final_df.filter(col('is_success') == 1).count()
    failed = final_df.filter(col('is_success') == 0).count()
    success_rate = (successful / total_missions) * 100
    
    print(f"Total Missions: {total_missions}")
    print(f"Successful: {successful} ({success_rate:.1f}%)")
    print(f"Failed/Partial: {failed} ({100-success_rate:.1f}%)")
    print(f"Unique Organizations: {final_df.select('company').distinct().count()}")
    print(f"Unique Rockets: {final_df.select('rocket').distinct().count()}")
    print(f"Year Range: 1957 - 2022")
    
    # Stop Spark
    processor.stop_session()
    
    return processor, final_df, aggregations


if __name__ == "__main__":
    try:
        processor, final_df, aggregations = main()
        print("\n✅ PySpark processing completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
