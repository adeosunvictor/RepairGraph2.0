from repairgraph.config import Settings


def test_settings_can_be_constructed():
    settings = Settings(
        _env_file=None,
        max_repair_attempts=5,
        max_agent_steps=35,
        max_llm_retries=3,
        llm_max_tokens=4096,
    )

    assert settings.max_repair_attempts == 5
    assert settings.max_agent_steps == 35
    assert settings.max_llm_retries == 3
    assert settings.llm_max_tokens == 4096