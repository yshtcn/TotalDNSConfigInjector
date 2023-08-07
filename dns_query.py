import dns.resolver
import configparser
import sys

def remove_quotes_if_present(s):
    """如果字符串的首尾都有引号，则去除它们。"""
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    elif s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    return s

def read_file_with_adaptive_encoding(filename):
    """尝试使用不同的编码读取文件。如果文件不存在，返回空字符串。"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filename, 'r', encoding='gbk') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def insert_between_markers(filename, marker, content):
    """在指定的标记之间插入内容，如果标记不存在，则在文件尾部添加标记和内容。"""
    start_marker = f"#{marker}_Start"
    end_marker = f"#{marker}_End"

    file_content = read_file_with_adaptive_encoding(filename)

    start_idx = file_content.find(start_marker)
    end_idx = file_content.find(end_marker)

    # 如果找不到开始或结束标记，则在文件尾部添加标记和内容
    if start_idx == -1 or end_idx == -1:
        file_content += '\n' + start_marker + '\n' + '\n'.join(content) + '\n' + end_marker + '\n'
    else:
        start_idx = file_content.find('\n', start_idx) + 1
        file_content = file_content[:start_idx] + '\n'.join(content) + '\n' + file_content[end_idx:]

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(file_content)

def get_dns_records_from_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    domain = config.get('DNS_QUERY', 'domain')
    nameservers = config.get('DNS_QUERY', 'nameservers').split(',')
    
    unique_ips = set()
    
    for nameserver in nameservers:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [nameserver.strip()]
        
        try:
            answers = resolver.resolve(domain, 'A')
            for answer in answers:
                unique_ips.add(answer.address)
        except Exception as e:
            print(f"Error querying from {nameserver}: {str(e)}")
    
    # 写入多个文件
    for section in config.sections():
        if section.startswith('OUTPUT_FILE_'):
            output_path = config.get(section, 'path')
            format_str = remove_quotes_if_present(config.get(section, 'format'))
            marker = config.get(section, 'marker')
            formatted_ips = [format_str.replace("{IP}", ip) for ip in unique_ips]
            insert_between_markers(output_path, marker, formatted_ips)
    
    return unique_ips

if __name__ == "__main__":
    # 使用命令行参数指定的配置文件，如果没有提供，则使用默认的 "config.ini"
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.ini"
    
    results = get_dns_records_from_config(config_file)
    for ip in results:
        print(ip)
