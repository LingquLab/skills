#!/usr/bin/env ruby

require "yaml"

ROOT = File.expand_path("..", __dir__)
SKILLS_ROOT = File.join(ROOT, "skills")
SCENARIOS_ROOT = File.join(ROOT, "tests", "scenarios")
EXPECTED_SKILLS = %w[
  superpowers-neo-brainstorming
  superpowers-neo-writing-plans
  superpowers-neo-using-git-worktrees
  superpowers-neo-executing-plans
  superpowers-neo-testing-strategy
  superpowers-neo-systematic-debugging
  superpowers-neo-requesting-code-review
  superpowers-neo-receiving-code-review
  superpowers-neo-verification-before-completion
  superpowers-neo-finishing-a-development-branch
].freeze
ALLOWED_FRONTMATTER_KEYS = %w[name description license allowed-tools metadata].freeze
REQUIRED_INTERFACE_KEYS = %w[display_name short_description default_prompt].freeze
EXPECTED_SCENARIOS = %w[
  01-clear-small-change.md
  02-complex-feature.md
  03-dirty-workspace.md
  04-subagent-execution.md
  05-risk-driven-testing.md
  06-systematic-debugging.md
  07-code-review.md
  08-verification-gap.md
  09-git-delivery.md
].freeze

def load_yaml(text, path)
  YAML.safe_load(text, permitted_classes: [], aliases: false) || {}
rescue Psych::SyntaxError => e
  raise "#{path}: invalid YAML: #{e.message.lines.first.strip}"
end

def extract_frontmatter(content, path)
  match = content.match(/\A---\n(.*?)\n---(?:\n|\z)/m)
  raise "#{path}: missing or invalid YAML frontmatter" unless match

  match[1]
end

def reject_duplicate_mapping_keys(text, path)
  stream = Psych.parse_stream(text, path)
  visit = lambda do |node|
    if node.is_a?(Psych::Nodes::Mapping)
      keys = []
      node.children.each_slice(2) do |key_node, value_node|
        raise "#{path}: mapping keys must be scalars" unless key_node.is_a?(Psych::Nodes::Scalar)

        key = key_node.value
        raise "#{path}: duplicate mapping key: #{key}" if keys.include?(key)

        keys << key
        visit.call(value_node)
      end
    elsif node.respond_to?(:children) && node.children
      node.children.each { |child| visit.call(child) }
    end
  end
  visit.call(stream)
rescue Psych::SyntaxError => e
  raise "#{path}: invalid YAML: #{e.message.lines.first.strip}"
end

def validate_skill(name)
  dir = File.join(SKILLS_ROOT, name)
  skill_path = File.join(dir, "SKILL.md")
  interface_path = File.join(dir, "agents", "openai.yaml")
  expected_files = [skill_path, interface_path].sort
  actual_files = Dir.glob(File.join(dir, "**", "*"), File::FNM_DOTMATCH)
    .select { |path| File.file?(path) }
    .sort

  raise "#{name}: expected only SKILL.md and agents/openai.yaml" unless actual_files == expected_files

  content = File.read(skill_path)
  frontmatter_text = extract_frontmatter(content, skill_path)
  reject_duplicate_mapping_keys(frontmatter_text, skill_path)
  frontmatter = load_yaml(frontmatter_text, skill_path)
  raise "#{skill_path}: frontmatter must be a mapping" unless frontmatter.is_a?(Hash)

  unexpected = frontmatter.keys.map(&:to_s) - ALLOWED_FRONTMATTER_KEYS
  raise "#{skill_path}: unexpected frontmatter keys: #{unexpected.join(', ')}" unless unexpected.empty?

  yaml_name = frontmatter["name"]
  description = frontmatter["description"]
  raise "#{skill_path}: name must match directory" unless yaml_name == name
  raise "#{skill_path}: invalid hyphen-case name" unless name.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/)
  raise "#{skill_path}: name exceeds 64 characters" if name.length > 64
  raise "#{skill_path}: description must be a non-empty string" unless description.is_a?(String) && !description.strip.empty?
  raise "#{skill_path}: description exceeds 1024 characters" if description.length > 1024
  raise "#{skill_path}: description contains angle brackets" if description.include?("<") || description.include?(">")
  raise "#{skill_path}: initializer placeholder remains" if content.match?(/\[TODO|PLACEHOLDER/)
  raise "#{skill_path}: original Superpowers namespace is forbidden" if content.include?("superpowers:")

  neo_references = content.scan(/superpowers-neo-[a-z0-9-]+/).uniq
  unknown_references = neo_references - EXPECTED_SKILLS
  raise "#{skill_path}: unknown Neo references: #{unknown_references.join(', ')}" unless unknown_references.empty?

  interface_text = File.read(interface_path)
  reject_duplicate_mapping_keys(interface_text, interface_path)
  interface_doc = load_yaml(interface_text, interface_path)
  interface = interface_doc["interface"]
  raise "#{interface_path}: interface must be a mapping" unless interface.is_a?(Hash)

  missing = REQUIRED_INTERFACE_KEYS - interface.keys.map(&:to_s)
  raise "#{interface_path}: missing interface keys: #{missing.join(', ')}" unless missing.empty?

  REQUIRED_INTERFACE_KEYS.each do |key|
    value = interface[key]
    raise "#{interface_path}: #{key} must be a non-empty string" unless value.is_a?(String) && !value.empty?
    key_lines = interface_text.lines.select { |line| line.match?(/^  #{Regexp.escape(key)}:/) }
    raise "#{interface_path}: #{key} must appear exactly once" unless key_lines.length == 1
    raise "#{interface_path}: #{key} must be double-quoted" unless key_lines.first.match?(/^  #{Regexp.escape(key)}: ".*"\s*$/)
  end

  short_description = interface["short_description"]
  unless (25..64).cover?(short_description.length)
    raise "#{interface_path}: short_description must contain 25-64 characters"
  end

  default_prompt = interface["default_prompt"]
  raise "#{interface_path}: default_prompt must mention $#{name}" unless default_prompt.include?("$#{name}")

  puts "ok: #{name}"
end

def validate_scenarios
  actual = Dir.children(SCENARIOS_ROOT).select do |entry|
    File.file?(File.join(SCENARIOS_ROOT, entry))
  end.sort
  unless actual == EXPECTED_SCENARIOS.sort
    missing = EXPECTED_SCENARIOS - actual
    extra = actual - EXPECTED_SCENARIOS
    raise "scenario inventory mismatch; missing=#{missing.inspect} extra=#{extra.inspect}"
  end

  EXPECTED_SCENARIOS.each do |name|
    path = File.join(SCENARIOS_ROOT, name)
    content = File.read(path)
    raise "#{path}: missing title" unless content.match?(/\A# .+\n/)

    section_pairs = content.scan(/^## ([^\n]+)\n(.*?)(?=^## |\z)/m)
    headings = section_pairs.map(&:first)
    duplicates = headings.group_by { |heading| heading }.select { |_heading, values| values.length > 1 }.keys
    raise "#{path}: duplicate sections: #{duplicates.join(', ')}" unless duplicates.empty?

    sections = section_pairs.to_h
    sections.each do |heading, body|
      raise "#{path}: empty section: #{heading}" if body.strip.empty?
    end

    skill_heading = sections.key?("Skill Under Test") ? "Skill Under Test" : "Skills Under Test"
    raise "#{path}: missing skill declaration" unless sections.key?(skill_heading)
    declared_skills = sections.fetch(skill_heading).scan(/`(superpowers-neo-[a-z0-9-]+)`/).flatten.uniq
    raise "#{path}: skill declaration is empty" if declared_skills.empty?
    unknown_skills = declared_skills - EXPECTED_SKILLS
    raise "#{path}: unknown declared skills: #{unknown_skills.join(', ')}" unless unknown_skills.empty?

    request_suffixes = headings.map do |heading|
      match = heading.match(/\ARequest(?: ([A-Z]))?(?:: .+)?\z/)
      match && (match[1] || "")
    end.compact
    raise "#{path}: missing request" if request_suffixes.empty?
    request_suffixes.each do |suffix|
      label = suffix.empty? ? "" : " #{suffix}"
      expected_heading = "Expected Behavior#{label}"
      failure_heading = "Failure Signals#{label}"
      raise "#{path}: missing #{expected_heading}" unless sections.key?(expected_heading)
      raise "#{path}: missing #{failure_heading}" unless sections.key?(failure_heading)
    end

    expected_suffixes = headings.map do |heading|
      match = heading.match(/\AExpected Behavior(?: ([A-Z]))?\z/)
      match && (match[1] || "")
    end.compact
    failure_suffixes = headings.map do |heading|
      match = heading.match(/\AFailure Signals(?: ([A-Z]))?\z/)
      match && (match[1] || "")
    end.compact
    unless expected_suffixes.sort == request_suffixes.sort && failure_suffixes.sort == request_suffixes.sort
      raise "#{path}: request, expected-behavior, and failure-signal variants must match"
    end

    raise "#{path}: placeholder remains" if content.match?(/\b(?:TBD|TODO|PLACEHOLDER)\b/)
  end
end

actual_skills = Dir.children(SKILLS_ROOT).select { |entry| File.directory?(File.join(SKILLS_ROOT, entry)) }.sort
unless actual_skills == EXPECTED_SKILLS.sort
  missing = EXPECTED_SKILLS - actual_skills
  extra = actual_skills - EXPECTED_SKILLS
  warn "error: skill inventory mismatch; missing=#{missing.inspect} extra=#{extra.inspect}"
  exit 1
end

begin
  EXPECTED_SKILLS.each { |name| validate_skill(name) }
  validate_scenarios
rescue StandardError => e
  warn "error: #{e.message}"
  exit 1
end

puts "validated #{EXPECTED_SKILLS.length} skills"
puts "validated #{EXPECTED_SCENARIOS.length} behavior scenario definitions"
