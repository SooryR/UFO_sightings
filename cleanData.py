import pandas as pd
import re
from dateutil import parser
import matplotlib.pyplot as plt
import seaborn as sns

def import_csv_pandas(filename):
    """Imports CSV using pandas.

    Args:
        filename: The path to the CSV file.

    Returns:
        A pandas DataFrame.
    """
    df = pd.read_csv(filename, encoding='utf-8', quotechar='"')
    return df

def custom_parse_datetime(dt_str):
    try:
      date_obj = parser.parse(dt_str, fuzzy=True) #fuzzy parsing
      if date_obj.hour == 24: #if hour is 24 fix it
          return datetime.datetime(date_obj.year, date_obj.month, date_obj.day + 1, 0, date_obj.minute, date_obj.second)
      else:
          return date_obj
    except ValueError:
      return None


def plot_shape_frequency_over_time(df):
    """
    Plots the frequency of different UFO shapes over time (grouped by year).

    Args:
        df (pd.DataFrame): The input DataFrame with UFO sighting data.
    """
    # Extract the year from the datetime
    df['year'] = df['datetime'].dt.year

    # Group by year and shape, count occurrences, and unstack the data
    year_shape_counts = df.groupby(['year', 'shape']).size().unstack(fill_value=0)

    # Create a line plot for each shape over time
    plt.figure(figsize=(12, 8))
    for shape in year_shape_counts.columns:
        year_shape_counts[shape].plot(label=shape, marker='o')

    plt.title('UFO Shape Frequency Over Time')
    plt.xlabel('Year')
    plt.ylabel('Frequency')
    plt.legend(title='Shape')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('shapeToYear.png')
    plt.close()
    

def plot_shape_frequency_by_state(df, top_n=10, output_dir=""):
    """
    Plots the frequency of shapes within each state using a dot plot,
    showing the top N most frequent shapes for each state all in one graph.

    Args:
        df (pd.DataFrame): The input DataFrame with UFO sighting data.
        top_n (int): The number of top shapes to show for each state.
    """

    # Group by state and shape, count the occurrences, and unstack the data
    state_shape_counts = df.groupby(['state', 'shape']).size().unstack(fill_value=0)

    # Get the top N shapes for each state
    top_shapes = state_shape_counts.apply(lambda x: x.nlargest(top_n).index.tolist(), axis=1)

    # Flatten the list of shapes and get the unique shapes
    all_top_shapes = list(set([shape for shapes in top_shapes for shape in shapes]))

    # Filter the counts to include only the top shapes for all states
    state_counts = state_shape_counts[all_top_shapes].fillna(0)

    # Create the dot plot
    plt.figure(figsize=(32, 20))
    for i, state in enumerate(state_counts.index):
        for j, shape in enumerate(all_top_shapes):
            count = state_counts.loc[state, shape]
            if count > 0:
              plt.scatter(i, j, s=(count**.9)*5, color=sns.color_palette('viridis', n_colors=len(all_top_shapes))[j], label = shape if i == 0 else "")

    plt.title(f'Top {top_n} UFO Shapes by State (All States)')
    plt.xlabel('State')
    plt.ylabel('Shape')
    plt.xticks(range(len(state_counts.index)), state_counts.index, rotation=45, ha='right')
    plt.yticks(range(len(all_top_shapes)), all_top_shapes)
    plt.legend(title='Shape')
    plt.grid(axis='x')
    plt.tight_layout()
    plt.savefig('all_states_to_shapes_dotplot.png')
    plt.close()
    

# Example usage:
csv_file_path = './complete.csv'
df = import_csv_pandas(csv_file_path)
df = df.drop('extra', axis=1)

# Print the data (for demonstration)
print(df)  # Or you can use print(df.head()) for the first few rows

# 1. Convert datetime column to datetime objects
df['datetime'] = df['datetime'].apply(custom_parse_datetime)
# 2. Handle missing state values: for now, fill with "unknown"
df['state'] = df['state'].fillna('unknown')
# 3. Handle missing country values
#   - If state is known and country is missing assume its US
df['country'] = df.apply(lambda row: 'us' if row['country'] is None and row['state'] != 'unknown' else row['country'], axis=1)
#   - If country is still missing and we have (uk/england) and (uk/wales) then set to 'gb'
df['country'] = df['country'].fillna('gb')
# 4. Standardize country codes
df['country'] = df['country'].replace('gb', 'uk')

# 5.  Standardize duration descriptions and keep duration in seconds
def standardize_duration(duration_str, duration_sec):
    if pd.notna(duration_sec):
        return duration_sec
    duration_str = duration_str.lower()
    minutes = 0
    seconds = 0
    if 'hr' in duration_str or 'hour' in duration_str:
        match_hr = re.search(r'(\d+)-?(\d*)?\s*(hr|hour)', duration_str)
        if match_hr:
            hrs = int(match_hr.group(1))
            minutes = hrs * 60
            if match_hr.group(2):
                 hrs2 = int(match_hr.group(2))
                 minutes = (minutes + (hrs2 * 60)) / 2  # Average the hrs
        else:
            match_min = re.search(r'(\d+)\s*(hr|hour)', duration_str)
            if match_min:
                minutes = int(match_min.group(1)) * 60
    if 'min' in duration_str or 'minute' in duration_str:
        match_min = re.search(r'(\d+)\s*(min|minute)', duration_str)
        if match_min:
            minutes = int(match_min.group(1))
    if 'sec' in duration_str or 'second' in duration_str:
       match_sec = re.search(r'(\d+)\s*(sec|second)', duration_str)
       if match_sec:
          seconds = int(match_sec.group(1))
    if 'about' in duration_str:
         minutes = minutes * 0.75 if minutes > 0 else seconds * 0.75
    if 'several' in duration_str:
       minutes = minutes * 4 if minutes > 0 else seconds * 4
    return  (minutes * 60) + seconds
df['duration_seconds'] = df.apply(lambda row: standardize_duration(row['duration (hours/min)'], row['duration (seconds)']), axis=1)
df = df.drop(['duration (seconds)', 'duration (hours/min)'], axis=1)

#6. Clean comments
def clean_text(text):
    if isinstance(text, str):
        text = re.sub(r'&#\d+;', '', text)  # Remove HTML entities
        text = re.sub(r'[^a-zA-Z0-9\s\.,\']', '', text) # remove special characters
        text = re.sub(r'\s+', ' ', text).strip()  # Replace extra spaces with single space
        return text
    else:
        return ''
df['comments'] = df['comments'].apply(clean_text)

plot_shape_frequency_by_state(df, top_n=10)
plot_shape_frequency_over_time(df)