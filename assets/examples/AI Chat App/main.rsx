<App>
  <Include src="./functions.rsx" />
  <Frame
    id="$main"
    isHiddenOnDesktop={false}
    isHiddenOnMobile={false}
    padding="8px 12px"
    paddingType="normal"
    sticky={false}
    type="main"
  >
    <Text
      id="pageTitle"
      marginType="normal"
      value="### AI Assistant"
      verticalAlign="center"
    />
    <Chat
      id="chatBox"
      _sessionStorageId="00000000-0000-0000-0000-000000000099"
      assistantName="AI Assistant"
      placeholder="Ask me anything..."
      queryTargetId="sendMessage"
      showAvatar={true}
      showEmptyState={true}
      showHeader={true}
      showTimestamp={true}
      emptyTitle="Welcome!"
      emptyDescription="Start a conversation with the AI assistant."
    />
  </Frame>
</App>
